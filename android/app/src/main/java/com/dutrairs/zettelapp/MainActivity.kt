package com.dutrairs.zettelapp

import android.content.Intent
import android.net.Uri
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.Check
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import androidx.lifecycle.lifecycleScope
import com.chaquo.python.PyObject
import com.chaquo.python.Python
import com.chaquo.python.android.AndroidPlatform
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

/** A row of the notes list, as returned by zettelapp.mobile.list_notes(). */
data class NoteRow(val id: String, val title: String)

/** The note currently open in the editor, as returned by read_note(). */
data class NoteDoc(val id: String, val title: String, val body: String)

class MainActivity : ComponentActivity() {

    private var isPythonReady by mutableStateOf(false)
    private var vaultPath by mutableStateOf<String?>(null)
    private var notes by mutableStateOf<List<NoteRow>>(emptyList())
    private var activeNote by mutableStateOf<NoteDoc?>(null)
    private var query by mutableStateOf("")
    private var pendingNoteId by mutableStateOf<String?>(null)

    private lateinit var mobile: PyObject

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        initPythonEngine()
        handleIncomingIntent(intent)

        setContent {
            MaterialTheme {
                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = MaterialTheme.colorScheme.background
                ) {
                    if (activeNote == null) NotesScreen() else EditorScreen(activeNote!!)
                }
            }
        }
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        setIntent(intent)
        handleIncomingIntent(intent)
    }

    private fun initPythonEngine() {
        if (!Python.isStarted()) {
            Python.start(AndroidPlatform(this))
        }
        val python = Python.getInstance()
        // Hand the app's private directories and this activity to the core.
        python.getModule("zettelapp.androidintegration")
            .callAttr("bootstrap", filesDir.absolutePath, cacheDir.absolutePath, this)
        mobile = python.getModule("zettelapp.mobile")
        isPythonReady = true
        openDefaultVault()
    }

    private fun handleIncomingIntent(intent: Intent?) {
        val uri: Uri? = intent?.data
        if (uri != null && uri.scheme == "zettelapp" && uri.host == "note") {
            val path = uri.path?.trim('/')
            if (!path.isNullOrEmpty()) {
                pendingNoteId = path
                if (vaultPath != null) openNote(path)
            }
        }
    }

    private fun openDefaultVault() {
        lifecycleScope.launch {
            val opened = withContext(Dispatchers.IO) {
                runCatching { mobile.callAttr("open_default_vault") }.getOrNull()
            }
            if (opened != null) {
                vaultPath = opened.get("path")?.toString()
                refreshNotes()
                pendingNoteId?.let { openNote(it) }
                pendingNoteId = null
            }
        }
    }

    private fun refreshNotes() {
        lifecycleScope.launch {
            notes = withContext(Dispatchers.IO) {
                mobile.callAttr("list_notes").asList().mapNotNull { row ->
                    val id = row.get("id")?.toString() ?: return@mapNotNull null
                    NoteRow(id, row.get("title")?.toString().orEmpty())
                }
            }
        }
    }

    fun openNote(noteId: String) {
        lifecycleScope.launch {
            activeNote = withContext(Dispatchers.IO) {
                val doc = mobile.callAttr("read_note", noteId)
                if (doc.get("error") != null) {
                    null
                } else {
                    NoteDoc(
                        id = doc.get("id").toString(),
                        title = doc.get("title")?.toString().orEmpty(),
                        body = doc.get("body")?.toString().orEmpty(),
                    )
                }
            }
        }
    }

    fun createNote() {
        lifecycleScope.launch {
            val created = withContext(Dispatchers.IO) {
                mobile.callAttr("create_note", getString(R.string.new_note_default_title), "")
            }
            refreshNotes()
            openNote(created.get("id").toString())
        }
    }

    fun saveNote(note: NoteDoc, title: String, body: String) {
        lifecycleScope.launch {
            withContext(Dispatchers.IO) {
                mobile.callAttr("save_note", note.id, title, body)
            }
            activeNote = null
            refreshNotes()
        }
    }

    // --- screens ---

    @OptIn(ExperimentalMaterial3Api::class)
    @Composable
    private fun NotesScreen() {
        val visible = notes.filter {
            query.isBlank() || it.title.contains(query, ignoreCase = true)
        }
        Scaffold(
            topBar = { TopAppBar(title = { Text(stringResource(R.string.app_name)) }) },
            floatingActionButton = {
                if (isPythonReady) {
                    FloatingActionButton(onClick = { createNote() }) {
                        Icon(
                            Icons.Filled.Add,
                            contentDescription = stringResource(R.string.new_note)
                        )
                    }
                }
            }
        ) { padding ->
            Column(modifier = Modifier.padding(padding).fillMaxSize()) {
                OutlinedTextField(
                    value = query,
                    onValueChange = { query = it },
                    modifier = Modifier.fillMaxWidth().padding(16.dp, 8.dp),
                    placeholder = { Text(stringResource(R.string.search_hint)) },
                    singleLine = true,
                )
                when {
                    !isPythonReady -> Box(
                        modifier = Modifier.fillMaxSize(),
                        contentAlignment = Alignment.Center
                    ) { CircularProgressIndicator() }

                    visible.isEmpty() -> Box(
                        modifier = Modifier.fillMaxSize(),
                        contentAlignment = Alignment.Center
                    ) { Text(stringResource(R.string.notes_empty)) }

                    else -> LazyColumn(modifier = Modifier.fillMaxSize()) {
                        items(visible) { row ->
                            ListItem(
                                headlineContent = { Text(row.title) },
                                modifier = Modifier.fillMaxWidth()
                                    .clickable { openNote(row.id) }
                            )
                            HorizontalDivider()
                        }
                    }
                }
            }
        }
    }

    @OptIn(ExperimentalMaterial3Api::class)
    @Composable
    private fun EditorScreen(note: NoteDoc) {
        var title by remember(note.id) { mutableStateOf(note.title) }
        var body by remember(note.id) { mutableStateOf(note.body) }
        Scaffold(
            topBar = {
                TopAppBar(
                    title = { Text(title.ifBlank { stringResource(R.string.app_name) }) },
                    actions = {
                        IconButton(onClick = { saveNote(note, title, body) }) {
                            Icon(
                                Icons.Filled.Check,
                                contentDescription = stringResource(R.string.save)
                            )
                        }
                    }
                )
            }
        ) { padding ->
            Column(modifier = Modifier.padding(padding).fillMaxSize()) {
                OutlinedTextField(
                    value = title,
                    onValueChange = { title = it },
                    modifier = Modifier.fillMaxWidth().padding(16.dp, 8.dp),
                    singleLine = true,
                )
                OutlinedTextField(
                    value = body,
                    onValueChange = { body = it },
                    modifier = Modifier.fillMaxWidth().padding(16.dp, 8.dp).fillMaxHeight(),
                )
            }
        }
    }
}
