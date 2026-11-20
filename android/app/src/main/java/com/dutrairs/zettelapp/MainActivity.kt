package com.dutrairs.zettelapp

import android.content.Intent
import android.net.Uri
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import com.chaquo.python.PyObject
import com.chaquo.python.Python
import com.chaquo.python.android.AndroidPlatform

class MainActivity : ComponentActivity() {

    private var activeNoteId by mutableStateOf<String?>(null)
    private var isPythonReady by mutableStateOf(false)

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
                    ZettelAppScreen(
                        isReady = isPythonReady,
                        noteId = activeNoteId,
                        onOpenNote = { id -> activeNoteId = id }
                    )
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
        isPythonReady = Python.isStarted()
    }

    private fun handleIncomingIntent(intent: Intent?) {
        val uri: Uri? = intent?.data
        if (uri != null && uri.scheme == "zettelapp") {
            if (uri.host == "note") {
                val path = uri.path?.trim('/')
                if (!path.isNullOrEmpty()) {
                    activeNoteId = path
                }
            }
        }
    }
}

@Composable
fun ZettelAppScreen(
    isReady: Boolean,
    noteId: String?,
    onOpenNote: (String) -> Unit
) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(24.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        Text(
            text = stringResource(R.string.app_name),
            style = MaterialTheme.typography.headlineLarge
        )
        Spacer(modifier = Modifier.height(16.dp))

        if (isReady) {
            Text(
                text = stringResource(R.string.python_initialized),
                style = MaterialTheme.typography.bodyLarge,
                color = MaterialTheme.colorScheme.primary
            )
        } else {
            CircularProgressIndicator()
        }

        Spacer(modifier = Modifier.height(24.dp))

        if (noteId != null) {
            Card(
                modifier = Modifier.fillMaxWidth()
            ) {
                Column(modifier = Modifier.padding(16.dp)) {
                    Text(
                        text = "Active Note ID:",
                        style = MaterialTheme.typography.labelMedium
                    )
                    Text(
                        text = noteId,
                        style = MaterialTheme.typography.titleMedium
                    )
                }
            }
        } else {
            Text(
                text = "No note currently opened.",
                style = MaterialTheme.typography.bodyMedium
            )
        }
    }
}
