package com.dutrairs.zettelapp

import android.content.Intent
import android.net.Uri
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.*
import androidx.compose.material.icons.outlined.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalConfiguration
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.lifecycleScope
import com.chaquo.python.PyObject
import com.chaquo.python.Python
import com.chaquo.python.android.AndroidPlatform
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.asCoroutineDispatcher
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import java.util.concurrent.Executors

// ---------------------------------------------------------------------------
// Data classes mirroring the JSON-friendly dicts returned by zettelapp.mobile
// ---------------------------------------------------------------------------

data class NoteRow(val id: String, val title: String, val modified: String, val tags: List<String>)
data class NoteDoc(
    val id: String,
    val title: String,
    val body: String,
    val tags: List<String>,
    val url: String,
    val created: String,
    val modified: String,
)
data class NoteLink(val id: String, val title: String, val type: String, val label: String, val color: String)
data class NoteDetails(val links: List<NoteLink>, val backlinks: List<NoteLink>, val cards: List<Pair<Int, String>>)
data class GraphNode(val id: String, val title: String, val tags: List<String>)
data class GraphEdge(val src: String, val dst: String, val type: String)
data class TagCount(val tag: String, val count: Int)
data class LinkTypeCount(val type: String, val label: String, val color: String, val count: Int)
data class MonthCount(val label: String, val count: Int)
data class Insights(
    val notes: Int, val links: Int, val tags: Int, val unlinked: Int,
    val cards: Int, val due: Int, val months: List<MonthCount>,
    val topTags: List<TagCount>, val linksByType: List<LinkTypeCount>,
)
data class ReviewCard(val id: Int, val noteId: String, val noteTitle: String, val front: String, val back: String)
data class ReviewDeck(val due: Int, val total: Int, val cards: List<ReviewCard>)
data class LinkTypeDef(val id: String, val label: String, val color: String, val directed: Boolean)

// Desktop-style palette: white/gray surfaces with a single blue accent.
private val AccentBlue = Color(0xFF1B5FD9)

private fun pyColor(hex: String): Color = runCatching {
    Color(android.graphics.Color.parseColor(hex))
}.getOrDefault(Color(0xFF898781))

private fun fmtDate(iso: String): String = runCatching {
    val parser = SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss", Locale.US)
    val date = parser.parse(iso.take(19)) ?: return ""
    SimpleDateFormat("d MMM yyyy", Locale.getDefault()).format(date)
}.getOrDefault("")

class MainActivity : ComponentActivity() {

    private var isPythonReady by mutableStateOf(false)
    private var isLoading by mutableStateOf(true)
    private var vaultPath by mutableStateOf<String?>(null)
    private var notes by mutableStateOf<List<NoteRow>>(emptyList())
    private var activeNote by mutableStateOf<NoteDoc?>(null)
    private var noteDetails by mutableStateOf<NoteDetails?>(null)
    private var query by mutableStateOf("")
    private var pendingNoteId by mutableStateOf<String?>(null)
    private var currentTab by mutableStateOf("notes")
    private var graphData by mutableStateOf(Pair(emptyList<GraphNode>(), emptyList<GraphEdge>()))
    private var linkTypes by mutableStateOf<List<LinkTypeDef>>(emptyList())
    private var insightsData by mutableStateOf<Insights?>(null)
    private var reviewDeck by mutableStateOf<ReviewDeck?>(null)
    private var appStatus by mutableStateOf<Map<String, String>>(emptyMap())

    // All Python (and its SQLite connection) must run on ONE thread:
    // sqlite3 objects refuse to cross threads, so a dedicated dispatcher keeps
    // every call on the same one regardless of which coroutine makes it.
    private val pyDispatcher = Executors.newSingleThreadExecutor().asCoroutineDispatcher()

    private lateinit var mobile: PyObject

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        initPythonEngine()
        handleIncomingIntent(intent)
        setContent { ZettelTheme { RootLayout() } }
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        setIntent(intent)
        handleIncomingIntent(intent)
    }

    // -- Python bridge -------------------------------------------------------

    private fun initPythonEngine() {
        if (!Python.isStarted()) Python.start(AndroidPlatform(this))
        val python = Python.getInstance()
        python.getModule("zettelapp.androidintegration")
            .callAttr("bootstrap", filesDir.absolutePath, cacheDir.absolutePath, this)
        mobile = python.getModule("zettelapp.mobile")
        isPythonReady = true
        openDefaultVault()
    }

    private fun handleIncomingIntent(intent: Intent?) {
        val uri = intent?.data ?: return
        if (uri.scheme == "zettelapp" && uri.host == "note") {
            val path = uri.path?.trim('/') ?: return
            if (path.isNotEmpty()) {
                pendingNoteId = path
                if (vaultPath != null) openNote(path)
            }
        }
    }

    private fun <T> py(block: () -> T): T? = runCatching { block() }.getOrElse {
        android.util.Log.e("ZettelPy", "Python call failed", it)
        null
    }

    /** Dict lookup that works reliably across Chaquopy versions. */
    private fun PyObject?.jget(key: String): PyObject? =
        this?.let { o ->
            @Suppress("UNCHECKED_CAST")
            val map = o.asMap() as Map<Any?, Any?>
            py { map[key] as PyObject? }
        }

    private fun rowFrom(obj: PyObject): NoteRow? {
        val id = obj.jget("id")?.toString() ?: return null
        val title = obj.jget("title")?.toString().orEmpty()
        val modified = obj.jget("modified")?.toString().orEmpty()
        val tags = obj.jget("tags")?.asList()?.map { it.toString() } ?: emptyList()
        return NoteRow(id, title, modified, tags)
    }

    private fun openDefaultVault() {
        lifecycleScope.launch {
            val opened = withContext(pyDispatcher) { py { mobile.callAttr("open_default_vault") } }
            if (opened != null) {
                vaultPath = opened.jget("path")?.toString()
                refreshNotes()
                pendingNoteId?.let { openNote(it) }
                pendingNoteId = null
            }
            isLoading = false
        }
    }

    private fun refreshNotes() {
        lifecycleScope.launch {
            notes = withContext(pyDispatcher) {
                py { mobile.callAttr("list_notes").asList() }
                    ?.mapNotNull { rowFrom(it) } ?: emptyList()
            }
        }
    }

    fun openNote(noteId: String) {
        lifecycleScope.launch {
            val doc = withContext(pyDispatcher) {
                py { mobile.callAttr("read_note", noteId) }
            } ?: return@launch
            if (doc.jget("error") != null) return@launch
            activeNote = NoteDoc(
                id = doc.jget("id").toString(),
                title = doc.jget("title")?.toString().orEmpty(),
                body = doc.jget("body")?.toString().orEmpty(),
                tags = doc.jget("tags")?.asList()?.map { it.toString() } ?: emptyList(),
                url = doc.jget("url")?.toString().orEmpty(),
                created = doc.jget("created")?.toString().orEmpty(),
                modified = doc.jget("modified")?.toString().orEmpty(),
            )
            loadNoteDetails(noteId)
        }
    }

    private fun loadNoteDetails(noteId: String) {
        lifecycleScope.launch {
            val d = withContext(pyDispatcher) { py { mobile.callAttr("note_details", noteId) } }
                ?: return@launch
            fun links(key: String): List<NoteLink> =
                d.jget(key)?.asList()?.mapNotNull { l ->
                    val id = l.jget("id")?.toString() ?: return@mapNotNull null
                    NoteLink(
                        id = id,
                        title = l.jget("title")?.toString().orEmpty(),
                        type = l.jget("type")?.toString().orEmpty(),
                        label = l.jget("label")?.toString().orEmpty(),
                        color = l.jget("color")?.toString().orEmpty(),
                    )
                } ?: emptyList()
            val cards = d.jget("cards")?.asList()?.mapNotNull { c ->
                val cid = py { c.jget("id")!!.toInt() } ?: return@mapNotNull null
                cid to (c.jget("front")?.toString().orEmpty())
            } ?: emptyList()
            noteDetails = NoteDetails(links("links"), links("backlinks"), cards)
        }
    }

    fun createNote() {
        lifecycleScope.launch {
            val created = withContext(pyDispatcher) {
                py { mobile.callAttr("create_note", getString(R.string.new_note_default_title), "") }
            }
            refreshNotes()
            created?.let { openNote(it.jget("id").toString()) }
        }
    }

    fun saveNote(noteId: String, title: String, body: String, tags: List<String>) {
        lifecycleScope.launch {
            withContext(pyDispatcher) {
                py { mobile.callAttr("save_note", noteId, title, body, tags) }
            }
            refreshNotes()
        }
    }

    fun trashNote(noteId: String) {
        lifecycleScope.launch {
            withContext(pyDispatcher) { py { mobile.callAttr("trash_note", noteId) } }
            activeNote = null
            noteDetails = null
            refreshNotes()
        }
    }

    private fun loadGraph() {
        lifecycleScope.launch {
            val data = withContext(pyDispatcher) { py { mobile.callAttr("get_graph") } }
                ?: return@launch
            val nList = data.jget("notes")?.asList()?.mapNotNull { item ->
                val id = item.jget("id")?.toString() ?: return@mapNotNull null
                GraphNode(
                    id,
                    item.jget("title")?.toString().orEmpty(),
                    item.jget("tags")?.asList()?.map { it.toString() } ?: emptyList(),
                )
            } ?: emptyList()
            val eList = data.jget("edges")?.asList()?.mapNotNull { item ->
                val src = item.jget("src")?.toString() ?: return@mapNotNull null
                val dst = item.jget("dst")?.toString() ?: return@mapNotNull null
                GraphEdge(src, dst, item.jget("type")?.toString().orEmpty())
            } ?: emptyList()
            graphData = Pair(nList, eList)
            val types = withContext(pyDispatcher) {
                py { mobile.callAttr("link_types").asList() }
            }?.mapNotNull { t ->
                val id = t.jget("id")?.toString() ?: return@mapNotNull null
                LinkTypeDef(
                    id,
                    t.jget("label")?.toString().orEmpty(),
                    t.jget("color")?.toString().orEmpty(),
                    t.jget("directed")?.toString()?.lowercase() == "true",
                )
            } ?: emptyList()
            linkTypes = types
        }
    }

    private fun loadInsights() {
        lifecycleScope.launch {
            val d = withContext(pyDispatcher) { py { mobile.callAttr("insights") } }
                ?: return@launch
            val months = d.jget("months")?.asList()?.mapNotNull { m ->
                MonthCount(
                    m.jget("label")?.toString().orEmpty(),
                    py { m.jget("count")!!.toInt() } ?: 0,
                )
            } ?: emptyList()
            val tags = d.jget("top_tags")?.asList()?.mapNotNull { t ->
                TagCount(
                    t.jget("tag")?.toString().orEmpty(),
                    py { t.jget("count")!!.toInt() } ?: 0,
                )
            } ?: emptyList()
            val byType = d.jget("links_by_type")?.asList()?.mapNotNull { t ->
                val type = t.jget("type")?.toString() ?: return@mapNotNull null
                LinkTypeCount(
                    type,
                    t.jget("label")?.toString().orEmpty(),
                    t.jget("color")?.toString().orEmpty(),
                    py { t.jget("count")!!.toInt() } ?: 0,
                )
            } ?: emptyList()
            insightsData = Insights(
                notes = py { d.jget("notes")!!.toInt() } ?: 0,
                links = py { d.jget("links")!!.toInt() } ?: 0,
                tags = py { d.jget("tags")!!.toInt() } ?: 0,
                unlinked = py { d.jget("unlinked")!!.toInt() } ?: 0,
                cards = py { d.jget("cards")!!.toInt() } ?: 0,
                due = py { d.jget("due")!!.toInt() } ?: 0,
                months = months, topTags = tags, linksByType = byType,
            )
        }
    }

    private fun loadReviewDeck() {
        lifecycleScope.launch {
            val d = withContext(pyDispatcher) { py { mobile.callAttr("review_deck") } }
                ?: return@launch
            val cards = d.jget("cards")?.asList()?.mapNotNull { c ->
                val id = py { c.jget("id")!!.toInt() } ?: return@mapNotNull null
                ReviewCard(
                    id = id,
                    noteId = c.jget("note_id")?.toString().orEmpty(),
                    noteTitle = c.jget("note_title")?.toString().orEmpty(),
                    front = c.jget("front")?.toString().orEmpty(),
                    back = c.jget("back")?.toString().orEmpty(),
                )
            } ?: emptyList()
            reviewDeck = ReviewDeck(
                py { d.jget("due")!!.toInt() } ?: 0,
                py { d.jget("total")!!.toInt() } ?: 0,
                cards,
            )
        }
    }

    fun gradeCard(cardId: Int, grade: Int) {
        lifecycleScope.launch { withContext(pyDispatcher) { py { mobile.callAttr("grade_card", cardId, grade) } } }
    }

    private fun loadStatus() {
        lifecycleScope.launch {
            val s = withContext(pyDispatcher) { py { mobile.callAttr("status") } } ?: return@launch
            val map = mutableMapOf<String, String>()
            py { s.asMap() }?.forEach { (k, v) -> map[k.toString()] = v?.toString().orEmpty() }
            appStatus = map
        }
    }
    // -- Theming -------------------------------------------------------------

    @Composable
    fun ZettelTheme(content: @Composable () -> Unit) {
        val dark = isSystemInDarkTheme()
        val scheme = if (dark) {
            darkColorScheme(
                primary = Color(0xFFA8C7FF),
                background = Color(0xFF15171B),
                surface = Color(0xFF1D2025),
                surfaceVariant = Color(0xFF262A31),
            )
        } else {
            lightColorScheme(
                primary = AccentBlue,
                background = Color(0xFFF4F5F7),
                surface = Color.White,
                surfaceVariant = Color(0xFFEDEFF3),
            )
        }
        MaterialTheme(colorScheme = scheme, content = content)
    }

    // -- Root ----------------------------------------------------------------

    @Composable
    fun RootLayout() {
        val isWide = LocalConfiguration.current.screenWidthDp >= 600
        if (isWide) {
            Scaffold(bottomBar = { BottomNav() }) { padding ->
                Row(Modifier.padding(padding).fillMaxSize()) {
                    Box(Modifier.weight(0.45f).fillMaxHeight()) { TabScreen() }
                    VerticalDivider()
                    Box(Modifier.weight(0.55f).fillMaxHeight()) {
                        val note = activeNote
                        if (note != null) EditorScreen(note, embedded = true) else EmptyDetail()
                    }
                }
            }
        } else {
            val note = activeNote
            Scaffold(bottomBar = { if (note == null) BottomNav() }) { padding ->
                Box(Modifier.padding(padding).fillMaxSize()) {
                    if (note != null) EditorScreen(note, embedded = false) else TabScreen()
                }
            }
        }
    }

    @Composable
    fun EmptyDetail() {
        Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
            Text("Select a note from the list", color = MaterialTheme.colorScheme.onSurfaceVariant)
        }
    }

    @Composable
    fun TabScreen() {
        when (currentTab) {
            "graph" -> GraphScreen()
            "insights" -> InsightsScreen()
            "review" -> ReviewScreen()
            "ask" -> AskScreen()
            else -> NotesScreen()
        }
    }

    @Composable
    fun BottomNav() {
        NavigationBar {
            listOf(
                Triple("notes", Icons.Filled.Description, "Notes"),
                Triple("graph", Icons.Filled.Hub, "Graph"),
                Triple("insights", Icons.Filled.Insights, "Insights"),
                Triple("review", Icons.Filled.School, "Review"),
                Triple("ask", Icons.Filled.Forum, "Ask"),
            ).forEach { (key, icon, label) ->
                NavigationBarItem(
                    selected = currentTab == key && activeNote == null,
                    onClick = {
                        currentTab = key
                        activeNote = null
                        when (key) {
                            "graph" -> if (graphData.first.isEmpty()) loadGraph()
                            "insights" -> loadInsights()
                            "review" -> loadReviewDeck()
                        }
                    },
                    icon = { Icon(icon, contentDescription = label) },
                    label = { Text(label) },
                )
            }
        }
    }

    // -- Notes list ----------------------------------------------------------

    @Composable
    fun NotesScreen() {
        var tagFilter by remember { mutableStateOf<String?>(null) }
        var showTagPicker by remember { mutableStateOf(false) }
        val visible = notes.filter { row ->
            val matchesQuery = query.isBlank() || row.title.contains(query, ignoreCase = true)
            val matchesTag = tagFilter == null || row.tags.any { it.equals(tagFilter, ignoreCase = true) }
            matchesQuery && matchesTag
        }
        val allTags = notes.flatMap { it.tags }.distinct().sorted()

        Box(Modifier.fillMaxSize()) {
            Column(Modifier.fillMaxSize()) {
            // Header row: title + tag filter
            Row(
                Modifier.fillMaxWidth().padding(start = 16.dp, end = 16.dp, top = 12.dp, bottom = 4.dp),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Text("Notes", style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.Bold)
                Text("  ${visible.size}", style = MaterialTheme.typography.titleMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
                Spacer(Modifier.weight(1f))
                TextButton(onClick = { showTagPicker = true }, enabled = allTags.isNotEmpty()) {
                    Icon(Icons.Filled.FilterList, null, Modifier.size(18.dp))
                    Text(tagFilter ?: "All tags")
                }
            }
            if (showTagPicker) {
                DropdownTagPicker(
                    tags = allTags,
                    selected = tagFilter,
                    onPick = { tagFilter = it; showTagPicker = false },
                    onDismiss = { showTagPicker = false },
                )
            }

            OutlinedTextField(
                value = query,
                onValueChange = { query = it },
                modifier = Modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 4.dp),
                placeholder = { Text(stringResource(R.string.search_hint)) },
                leadingIcon = { Icon(Icons.Filled.Search, null) },
                singleLine = true,
                shape = RoundedCornerShape(24.dp),
            )

            when {
                !isPythonReady || isLoading -> Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                    CircularProgressIndicator()
                }
                visible.isEmpty() -> Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                    Text(stringResource(R.string.notes_empty), color = MaterialTheme.colorScheme.onSurfaceVariant)
                }
                else -> LazyColumn(Modifier.fillMaxSize()) {
                    items(visible) { row ->
                        NoteListItem(row)
                        HorizontalDivider(color = MaterialTheme.colorScheme.surfaceVariant)
                    }
                }
            }
            }
            FloatingActionButton(
                onClick = { createNote() },
                modifier = Modifier.align(Alignment.BottomEnd).padding(16.dp),
                shape = CircleShape,
            ) {
                Icon(Icons.Filled.Add, contentDescription = stringResource(R.string.new_note))
            }
        }
    }

    @Composable
    fun DropdownTagPicker(tags: List<String>, selected: String?, onPick: (String?) -> Unit, onDismiss: () -> Unit) {
        androidx.compose.foundation.lazy.LazyRow(
            Modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 4.dp),
            horizontalArrangement = Arrangement.spacedBy(6.dp),
        ) {
            item {
                SuggestionChip(onClick = { onPick(null) }, label = { Text("All") }, enabled = selected != null)
            }
            items(tags) { tag ->
                SuggestionChip(onClick = { onPick(tag) }, label = { Text("#$tag") }, enabled = selected != tag)
            }
        }
    }

    @Composable
    fun NoteListItem(row: NoteRow) {
        val selected = activeNote?.id == row.id
        ListItem(
            headlineContent = {
                Text(
                    row.title.ifBlank { "Untitled" },
                    fontWeight = if (selected) FontWeight.Bold else FontWeight.Medium,
                    maxLines = 1, overflow = TextOverflow.Ellipsis,
                )
            },
            supportingContent = {
                Column {
                    if (row.tags.isNotEmpty()) {
                        Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                            row.tags.take(3).forEach { TagPill(it) }
                        }
                        Spacer(Modifier.height(2.dp))
                    }
                    Text(fmtDate(row.modified), style = MaterialTheme.typography.bodySmall)
                }
            },
            leadingContent = {
                Box(Modifier.size(12.dp).background(AccentBlue.copy(alpha = if (selected) 1f else 0.35f), CircleShape))
            },
            modifier = Modifier.fillMaxWidth().clickable { openNote(row.id) },
        )
    }

    @Composable
    fun TagPill(tag: String, onRemove: (() -> Unit)? = null) {
        Surface(
            color = AccentBlue.copy(alpha = 0.12f),
            shape = RoundedCornerShape(50),
        ) {
            Row(
                Modifier.padding(start = 8.dp, end = if (onRemove != null) 2.dp else 8.dp, top = 2.dp, bottom = 2.dp),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Text("#$tag", style = MaterialTheme.typography.labelSmall, color = AccentBlue)
                if (onRemove != null) {
                    Icon(
                        Icons.Filled.Close, "Remove tag",
                        Modifier.size(14.dp).clickable { onRemove() },
                        tint = AccentBlue,
                    )
                }
            }
        }
    }

    // -- Editor --------------------------------------------------------------

    @OptIn(ExperimentalMaterial3Api::class)
    @Composable
    fun EditorScreen(note: NoteDoc, embedded: Boolean) {
        var title by remember(note.id) { mutableStateOf(note.title) }
        var body by remember(note.id) { mutableStateOf(note.body) }
        val tags = remember(note.id, note.tags) { mutableStateListOf<String>().apply { addAll(note.tags) } }
        var newTag by remember { mutableStateOf("") }
        var showPreview by remember { mutableStateOf(false) }
        var showDeleteConfirm by remember { mutableStateOf(false) }

        Scaffold(
            containerColor = MaterialTheme.colorScheme.surface,
            topBar = {
                TopAppBar(
                    title = { Text(note.title.ifBlank { "Untitled" }, maxLines = 1, overflow = TextOverflow.Ellipsis) },
                    navigationIcon = {
                        if (!embedded) {
                            IconButton(onClick = {
                                saveNote(note.id, title, body, tags)
                                activeNote = null
                                noteDetails = null
                            }) { Icon(Icons.AutoMirrored.Filled.ArrowBack, "Back") }
                        }
                    },
                    actions = {
                        if (showPreview.not()) IconButton(onClick = { showPreview = true }) {
                            Icon(Icons.Outlined.Visibility, "Preview")
                        } else IconButton(onClick = { showPreview = false }) {
                            Icon(Icons.Filled.Edit, "Edit")
                        }
                        IconButton(onClick = { showDeleteConfirm = true }) {
                            Icon(Icons.Outlined.Delete, "Move to trash")
                        }
                        IconButton(onClick = {
                            saveNote(note.id, title, body, tags)
                            if (!embedded) { activeNote = null; noteDetails = null }
                        }) { Icon(Icons.Filled.Check, stringResource(R.string.save)) }
                    }
                )
            },
        ) { padding ->
            Column(Modifier.padding(padding).fillMaxSize()) {
                // Metadata line
                Text(
                    "Created ${fmtDate(note.created)} · Edited ${fmtDate(note.modified)} · ID ${note.id}",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    modifier = Modifier.padding(horizontal = 16.dp),
                )
                if (note.url.isNotEmpty()) {
                    Text(
                        note.url,
                        style = MaterialTheme.typography.bodySmall,
                        color = AccentBlue,
                        modifier = Modifier.padding(horizontal = 16.dp, vertical = 2.dp)
                            .clickable { runCatching { startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(note.url))) } },
                        maxLines = 1, overflow = TextOverflow.Ellipsis,
                    )
                }

                if (showPreview) {
                    NotePreview(title, body, Modifier.weight(1f))
                } else {
                    Column(Modifier.weight(1f).padding(horizontal = 16.dp)) {
                        OutlinedTextField(
                            value = title, onValueChange = { title = it },
                            modifier = Modifier.fillMaxWidth().padding(top = 8.dp),
                            label = { Text("Title") }, singleLine = true,
                            textStyle = MaterialTheme.typography.titleLarge,
                        )
                        Spacer(Modifier.height(8.dp))
                        // Tag chips
                        Row(
                            Modifier.fillMaxWidth().horizontalScroll(rememberScrollState()),
                            horizontalArrangement = Arrangement.spacedBy(6.dp),
                            verticalAlignment = Alignment.CenterVertically,
                        ) {
                            tags.forEach { tag -> TagPill(tag) { tags.remove(tag) } }
                            OutlinedTextField(
                                value = newTag,
                                onValueChange = { newTag = it.trimStart('#') },
                                modifier = Modifier.width(110.dp),
                                placeholder = { Text("Add tag", style = MaterialTheme.typography.labelSmall) },
                                textStyle = MaterialTheme.typography.labelSmall,
                                singleLine = true,
                                shape = RoundedCornerShape(50),
                            )
                        }
                        Spacer(Modifier.height(8.dp))
                        OutlinedTextField(
                            value = body, onValueChange = { body = it },
                            modifier = Modifier.fillMaxWidth().weight(1f),
                            label = { Text("Body — Markdown, #tags, [[Links]], Q:/A: cards") },
                        )
                    }
                }

                // Links / backlinks / flashcards section
                val details = noteDetails
                if (details != null && !showPreview) {
                    HorizontalDivider()
                    Column(
                        Modifier.weight(0.35f).verticalScroll(rememberScrollState()).padding(16.dp)
                    ) {
                        if (details.links.isNotEmpty()) {
                            Text("Links", fontWeight = FontWeight.SemiBold, style = MaterialTheme.typography.titleSmall)
                            details.links.forEach { l ->
                                LinkRow(l) { openNote(l.id) }
                            }
                        }
                        if (details.backlinks.isNotEmpty()) {
                            Spacer(Modifier.height(8.dp))
                            Text("Backlinks", fontWeight = FontWeight.SemiBold, style = MaterialTheme.typography.titleSmall)
                            details.backlinks.forEach { l -> LinkRow(l) { openNote(l.id) } }
                        }
                        if (details.cards.isNotEmpty()) {
                            Spacer(Modifier.height(8.dp))
                            Text(
                                "Flashcards (${details.cards.size})",
                                fontWeight = FontWeight.SemiBold, style = MaterialTheme.typography.titleSmall,
                            )
                            details.cards.forEach { (_, front) ->
                                Text("• $front", style = MaterialTheme.typography.bodySmall)
                            }
                        }
                    }
                }
            }
        }

        if (showDeleteConfirm) {
            AlertDialog(
                onDismissRequest = { showDeleteConfirm = false },
                title = { Text("Move to trash?") },
                text = { Text("“${note.title.ifBlank { "Untitled" }}” will be moved to the trash.") },
                confirmButton = {
                    TextButton(onClick = { showDeleteConfirm = false; trashNote(note.id) }) { Text("Trash") }
                },
                dismissButton = {
                    TextButton(onClick = { showDeleteConfirm = false }) { Text("Cancel") }
                },
            )
        }
    }

    @Composable
    fun LinkRow(link: NoteLink, onClick: () -> Unit) {
        Row(
            Modifier.fillMaxWidth().clickable(onClick = onClick).padding(vertical = 4.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Box(Modifier.size(8.dp).background(pyColor(link.color), CircleShape))
            Spacer(Modifier.width(8.dp))
            Text(link.title, style = MaterialTheme.typography.bodyMedium)
            Spacer(Modifier.width(8.dp))
            Text(link.label, style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
        }
    }

    /** Very small markdown-ish renderer: bold, italic, [[links]] as chips. */
    @Composable
    fun NotePreview(title: String, body: String, modifier: Modifier) {
        Column(modifier.verticalScroll(rememberScrollState()).padding(16.dp)) {
            Text(title, style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.Bold)
            Spacer(Modifier.height(12.dp))
            body.lines().forEach { line ->
                val trimmed = line.trim()
                when {
                    trimmed.startsWith("# ") -> Text(
                        trimmed.drop(2), style = MaterialTheme.typography.titleLarge,
                        fontWeight = FontWeight.SemiBold, modifier = Modifier.padding(vertical = 4.dp),
                    )
                    trimmed.startsWith("## ") -> Text(
                        trimmed.drop(3), style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.SemiBold, modifier = Modifier.padding(vertical = 4.dp),
                    )
                    trimmed.startsWith("- ") || trimmed.startsWith("* ") -> Text(
                        "•  ${trimmed.drop(2)}",
                        style = MaterialTheme.typography.bodyMedium, modifier = Modifier.padding(start = 8.dp, bottom = 2.dp),
                    )
                    trimmed.startsWith("Q:") -> Card(
                        colors = CardDefaults.cardColors(containerColor = AccentBlue.copy(alpha = 0.08f)),
                        modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp),
                    ) {
                        Column(Modifier.padding(12.dp)) {
                            Text(trimmed, fontWeight = FontWeight.SemiBold, style = MaterialTheme.typography.bodyMedium)
                            body.lines().dropWhile { it.trim() != trimmed }.drop(1)
                                .takeWhile { it.trim().startsWith("A:") }
                                .forEach { Text(it.trim(), style = MaterialTheme.typography.bodyMedium) }
                        }
                    }
                    trimmed.startsWith("A:") -> {}
                    else -> Text(line, style = MaterialTheme.typography.bodyMedium)
                }
            }
        }
    }

    // -- Graph ---------------------------------------------------------------

    private fun tagColor(tag: String): Color {
        // Deterministic tag color, in the spirit of the desktop cluster palette.
        val palette = listOf(
            Color(0xFF2A78D6), Color(0xFFE8833A), Color(0xFF008300), Color(0xFF6250D6),
            Color(0xFFE34948), Color(0xFFEDA100), Color(0xFF1BAF7A), Color(0xFFB0417A),
        )
        return palette[Math.abs(tag.hashCode()) % palette.size]
    }

    @Composable
    fun GraphScreen() {
        Column(Modifier.fillMaxSize()) {
            Row(
                Modifier.fillMaxWidth().padding(start = 16.dp, end = 16.dp, top = 12.dp),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Text("Graph", style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.Bold)
                Spacer(Modifier.weight(1f))
                Text(
                    "${graphData.first.size} notes · ${graphData.second.size} links",
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    style = MaterialTheme.typography.bodyMedium,
                )
                IconButton(onClick = { loadGraph() }) { Icon(Icons.Filled.Refresh, "Refresh") }
            }
            if (graphData.first.isEmpty()) {
                Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) { CircularProgressIndicator() }
            } else {
                var selected by remember { mutableStateOf<GraphNode?>(null) }
                Box(Modifier.fillMaxSize()) {
                    GraphCanvas(onNodeTap = { selected = it })
                    selected?.let { node ->
                        Card(
                            modifier = Modifier.align(Alignment.BottomCenter).padding(16.dp).fillMaxWidth(),
                        ) {
                            Row(
                                Modifier.padding(12.dp),
                                verticalAlignment = Alignment.CenterVertically,
                            ) {
                                Column(Modifier.weight(1f)) {
                                    Text(node.title.ifBlank { "Untitled" }, fontWeight = FontWeight.SemiBold)
                                    if (node.tags.isNotEmpty()) {
                                        Text("#" + node.tags.joinToString(" #"), style = MaterialTheme.typography.bodySmall)
                                    }
                                }
                                Button(onClick = { openNote(node.id) }) { Text("Open") }
                            }
                        }
                    }
                }
            }
        }
    }

    @Composable
    fun GraphCanvas(onNodeTap: (GraphNode) -> Unit) {
        val nodes = graphData.first
        val edges = graphData.second
        BoxWithConstraints(Modifier.fillMaxSize()) {
            val w = maxWidth.value
            val h = maxHeight.value
            val positions = remember(nodes, w, h) {
                // Simple ring layout, grouped by primary tag so clusters sit together.
                val sorted = nodes.sortedBy { it.tags.firstOrNull() ?: "" }
                val radius = minOf(w, h) * 0.36f
                val cx = w / 2f
                val cy = h / 2f
                sorted.indices.associate { i ->
                    val angle = 2.0 * Math.PI * i / sorted.size
                    sorted[i].id to Offset(
                        cx + (radius * Math.cos(angle)).toFloat(),
                        cy + (radius * Math.sin(angle)).toFloat(),
                    )
                }
            }
            val density = LocalDensity.current
            Canvas(Modifier.fillMaxSize().clickable { }) {
                val nodeById = nodes.associateBy { it.id }
                edges.forEach { edge ->
                    val p1 = positions[edge.src]
                    val p2 = positions[edge.dst]
                    if (p1 != null && p2 != null) {
                        val lt = linkTypes.firstOrNull { it.id == edge.type }
                        drawLine(
                            (lt?.let { pyColor(it.color) } ?: Color(0xFF898781)).copy(alpha = 0.55f),
                            p1 * density.density, p2 * density.density, strokeWidth = 4f,
                        )
                    }
                }
                positions.forEach { (id, pos) ->
                    val node = nodeById[id] ?: return@forEach
                    val color = node.tags.firstOrNull()?.let { tagColor(it) } ?: AccentBlue
                    drawCircle(color, radius = 26f, center = pos * density.density)
                    drawCircle(Color.White, radius = 10f, center = pos * density.density)
                }
            }
            // Tap targets + labels overlay
            positions.forEach { (id, pos) ->
                val node = nodes.firstOrNull { it.id == id } ?: return@forEach
                val px = with(density) { (pos.x).dp }
                val py = with(density) { (pos.y).dp }
                Box(
                    Modifier
                        .offset(x = px - 22.dp, y = py - 22.dp)
                        .size(44.dp)
                        .clickable { onNodeTap(node) },
                )
                Text(
                    node.title.ifBlank { "Untitled" },
                    style = MaterialTheme.typography.labelSmall,
                    maxLines = 1,
                    modifier = Modifier.offset(x = px - 55.dp, y = py + 24.dp).width(110.dp),
                    textAlign = androidx.compose.ui.text.style.TextAlign.Center,
                )
            }
        }
    }

    // -- Insights ------------------------------------------------------------

    @Composable
    fun InsightsScreen() {
        val d = insightsData
        if (d == null) {
            Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) { CircularProgressIndicator() }
            return
        }
        Column(
            Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(16.dp)
        ) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text("Insights", style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.Bold)
                Spacer(Modifier.weight(1f))
                IconButton(onClick = { loadInsights() }) { Icon(Icons.Filled.Refresh, "Refresh") }
            }
            Spacer(Modifier.height(8.dp))
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                StatCard("Notes", d.notes, Modifier.weight(1f))
                StatCard("Links", d.links, Modifier.weight(1f))
                StatCard("Tags", d.tags, Modifier.weight(1f))
            }
            Spacer(Modifier.height(8.dp))
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                StatCard("Unlinked", d.unlinked, Modifier.weight(1f))
                StatCard("Flashcards", d.cards, Modifier.weight(1f))
                StatCard("Due", d.due, Modifier.weight(1f))
            }
            Spacer(Modifier.height(16.dp))
            ChartCard("Notes added per month") {
                BarChart(d.months.map { it.label to it.count })
            }
            Spacer(Modifier.height(16.dp))
            ChartCard("Top tags") {
                HBarList(d.topTags.map { it.tag to it.count }, color = AccentBlue)
            }
            Spacer(Modifier.height(16.dp))
            ChartCard("Links by type") {
                Column {
                    d.linksByType.forEach { lt ->
                        Row(Modifier.fillMaxWidth().padding(vertical = 3.dp), verticalAlignment = Alignment.CenterVertically) {
                            Box(Modifier.size(10.dp).background(pyColor(lt.color), CircleShape))
                            Spacer(Modifier.width(8.dp))
                            Text(lt.label, Modifier.width(100.dp), style = MaterialTheme.typography.bodySmall, maxLines = 1)
                            HBar(lt.count, d.linksByType.maxOf { it.count }, pyColor(lt.color), Modifier.weight(1f))
                            Spacer(Modifier.width(6.dp))
                            Text("${lt.count}", style = MaterialTheme.typography.labelSmall)
                        }
                    }
                }
            }
            Spacer(Modifier.height(24.dp))
        }
    }

    @Composable
    fun StatCard(label: String, value: Int, modifier: Modifier = Modifier) {
        Card(modifier) {
            Column(Modifier.padding(12.dp)) {
                Text("$value", style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.Bold, color = AccentBlue)
                Text(label, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
            }
        }
    }

    @Composable
    fun ChartCard(title: String, content: @Composable () -> Unit) {
        Card(Modifier.fillMaxWidth()) {
            Column(Modifier.padding(12.dp)) {
                Text(title, fontWeight = FontWeight.SemiBold, style = MaterialTheme.typography.titleSmall)
                Spacer(Modifier.height(10.dp))
                content()
            }
        }
    }

    @Composable
    fun BarChart(data: List<Pair<String, Int>>) {
        val max = data.maxOfOrNull { it.second }?.coerceAtLeast(1) ?: 1
        Row(
            Modifier.fillMaxWidth().height(120.dp),
            verticalAlignment = Alignment.Bottom,
            horizontalArrangement = Arrangement.spacedBy(4.dp),
        ) {
            data.forEach { (label, count) ->
                Column(Modifier.weight(1f), horizontalAlignment = Alignment.CenterHorizontally) {
                    Box(
                        Modifier.fillMaxWidth()
                            .height((count.toFloat() / max * 90).dp.coerceAtLeast(2.dp))
                            .background(AccentBlue, RoundedCornerShape(3.dp)),
                    )
                    Text(label, style = MaterialTheme.typography.labelSmall, maxLines = 1)
                }
            }
        }
    }

    @Composable
    fun HBar(value: Int, max: Int, color: Color, modifier: Modifier = Modifier) {
        val fraction = (value.toFloat() / max.coerceAtLeast(1)).coerceIn(0f, 1f)
        Box(
            modifier.height(8.dp)
                .background(MaterialTheme.colorScheme.surfaceVariant, RoundedCornerShape(4.dp))
        ) {
            Box(
                Modifier.fillMaxHeight()
                    .fillMaxWidth(fraction)
                    .background(color, RoundedCornerShape(4.dp))
            )
        }
    }

    @Composable
    fun HBarList(data: List<Pair<String, Int>>, color: Color) {
        val max = data.maxOfOrNull { it.second }?.coerceAtLeast(1) ?: 1
        Column {
            data.forEach { (tag, count) ->
                Row(Modifier.fillMaxWidth().padding(vertical = 3.dp), verticalAlignment = Alignment.CenterVertically) {
                    Text("#$tag", Modifier.width(110.dp), style = MaterialTheme.typography.bodySmall, maxLines = 1)
                    HBar(count, max, color, Modifier.weight(1f))
                    Spacer(Modifier.width(6.dp))
                    Text("$count", style = MaterialTheme.typography.labelSmall)
                }
            }
        }
    }

    // -- Review (spaced repetition) ------------------------------------------

    @Composable
    fun ReviewScreen() {
        val deck = reviewDeck
        if (deck == null) {
            Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) { CircularProgressIndicator() }
            return
        }
        var session by remember { mutableStateOf<List<ReviewCard>>(emptyList()) }
        var index by remember { mutableIntStateOf(0) }
        var revealed by remember { mutableStateOf(false) }

        if (session.isEmpty()) {
            Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(16.dp)) {
                Text("Review", style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.Bold)
                Spacer(Modifier.height(12.dp))
                Card(Modifier.fillMaxWidth()) {
                    Column(Modifier.padding(16.dp)) {
                        Text(
                            "${deck.due}",
                            style = MaterialTheme.typography.displaySmall,
                            fontWeight = FontWeight.Bold, color = AccentBlue,
                        )
                        Text("of ${deck.total} flashcards due today", color = MaterialTheme.colorScheme.onSurfaceVariant)
                        Spacer(Modifier.height(12.dp))
                        Button(
                            onClick = { session = deck.cards; index = 0; revealed = false },
                            enabled = deck.cards.isNotEmpty(),
                            modifier = Modifier.fillMaxWidth(),
                        ) {
                            Icon(Icons.Filled.PlayArrow, null)
                            Text("Start review")
                        }
                    }
                }
                Spacer(Modifier.height(16.dp))
                Card(Modifier.fillMaxWidth()) {
                    Column(Modifier.padding(16.dp)) {
                        Text("Anki export", fontWeight = FontWeight.SemiBold)
                        Spacer(Modifier.height(4.dp))
                        Text(
                            "Deck export (.apkg) and AnkiConnect sync are available from the desktop app.",
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                        )
                    }
                }
            }
        } else {
            val card = session.getOrNull(index)
            if (card == null) {
                // Session finished
                Column(
                    Modifier.fillMaxSize().padding(24.dp),
                    verticalArrangement = Arrangement.Center,
                    horizontalAlignment = Alignment.CenterHorizontally,
                ) {
                    Icon(Icons.Filled.TaskAlt, null, Modifier.size(56.dp), tint = AccentBlue)
                    Spacer(Modifier.height(12.dp))
                    Text("Session complete!", style = MaterialTheme.typography.titleLarge)
                    Spacer(Modifier.height(16.dp))
                    Button(onClick = { session = emptyList(); loadReviewDeck() }) { Text("Done") }
                }
            } else {
                Column(Modifier.fillMaxSize().padding(16.dp)) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        TextButton(onClick = { session = emptyList() }) { Text("End session") }
                        Spacer(Modifier.weight(1f))
                        Text("${index + 1} / ${session.size}", color = MaterialTheme.colorScheme.onSurfaceVariant)
                    }
                    LinearProgressIndicator(
                        progress = { (index + 1f) / session.size },
                        modifier = Modifier.fillMaxWidth(),
                    )
                    Spacer(Modifier.height(16.dp))
                    Text(card.noteTitle, style = MaterialTheme.typography.labelMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
                    Spacer(Modifier.height(8.dp))
                    Card(Modifier.fillMaxWidth()) {
                        Column(Modifier.padding(16.dp)) {
                            Text(card.front, style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.SemiBold)
                            if (revealed) {
                                HorizontalDivider(Modifier.padding(vertical = 12.dp))
                                Text(card.back, style = MaterialTheme.typography.bodyLarge)
                            }
                        }
                    }
                    Spacer(Modifier.weight(1f))
                    if (!revealed) {
                        Button(
                            onClick = { revealed = true },
                            modifier = Modifier.fillMaxWidth(),
                        ) { Text("Show answer") }
                    } else {
                        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                            OutlinedButton(
                                onClick = { gradeCard(card.id, 0); index++; revealed = false },
                                modifier = Modifier.weight(1f),
                            ) { Text("Again") }
                            Button(
                                onClick = { gradeCard(card.id, 1); index++; revealed = false },
                                modifier = Modifier.weight(1f),
                            ) { Text("Good") }
                            FilledTonalButton(
                                onClick = { gradeCard(card.id, 2); index++; revealed = false },
                                modifier = Modifier.weight(1f),
                            ) { Text("Easy") }
                        }
                    }
                }
            }
        }
    }

    // -- Ask -----------------------------------------------------------------

    @Composable
    fun AskScreen() {
        Column(Modifier.fillMaxSize().padding(16.dp)) {
            Text("Ask your notes", style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.Bold)
            Spacer(Modifier.height(8.dp))
            Card(colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)) {
                Column(Modifier.padding(16.dp)) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Icon(Icons.Outlined.Info, null, Modifier.size(18.dp), tint = MaterialTheme.colorScheme.onSurfaceVariant)
                        Spacer(Modifier.width(8.dp))
                        Text("AI question answering", fontWeight = FontWeight.SemiBold)
                    }
                    Spacer(Modifier.height(6.dp))
                    Text(
                        "AI-powered Q&A needs an API key and is currently configured from the desktop app. " +
                            "Use the search field on the Notes tab to find notes in the meantime.",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                }
            }
        }
    }
}
