package com.example.appdjango

import android.os.Bundle
import android.view.View // Import necessário para referenciar View.GONE, etc.
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.appcompat.app.AppCompatActivity
import com.chaquo.python.Python
import com.chaquo.python.android.AndroidPlatform
import java.net.InetSocketAddress
import java.net.Socket

class MainActivity : AppCompatActivity() {

    private lateinit var myWebView: WebView
    private var serverStarted = false

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        myWebView = findViewById(R.id.webView)

        // Configurações do WebView
        myWebView.settings.javaScriptEnabled = true
        myWebView.settings.domStorageEnabled = true
        myWebView.settings.allowFileAccess = true
        myWebView.settings.allowContentAccess = true
        myWebView.settings.allowFileAccessFromFileURLs = true
        myWebView.settings.allowUniversalAccessFromFileURLs = true
        myWebView.webViewClient = WebViewClient()

        // 1. Carregar a tela de loading HTML local IMEDIATAMENTE
        myWebView.loadUrl("file:///android_asset/loading.html")

        // 2. Inicia o Python/Django
        startDjangoServer()

        // 3. Monitora o servidor
        waitForServerAndLoad()
    }

    private fun startDjangoServer() {
        if (!Python.isStarted()) {
            Python.start(AndroidPlatform(this))
        }

        Thread {
            try {
                val python = Python.getInstance()
                val pythonModule = python.getModule("app_main")
                pythonModule.callAttr("start_server")
            } catch (e: Exception) {
                e.printStackTrace()
            }
        }.start()
    }

    private fun waitForServerAndLoad() {
        Thread {
            var attempts = 0
            // Espera até 60 segundos (240 tentativas * 250ms)
            while (!serverStarted && attempts < 240) {
                try {
                    val socket = Socket()
                    socket.connect(InetSocketAddress("127.0.0.1", 8000), 200)
                    socket.close()
                    serverStarted = true
                } catch (e: Exception) {
                    Thread.sleep(250)
                    attempts++
                }
            }

            runOnUiThread {
                if (serverStarted) {
                    // Servidor pronto: troca o loading pelo Django
                    myWebView.loadUrl("http://127.0.0.1:8000")
                } else {
                    myWebView.loadData("<html><body><h1>Erro: Servidor Django não iniciou.</h1></body></html>", "text/html", "UTF-8")
                }
            }
        }.start()
    }

    override fun onBackPressed() {
        if (myWebView.canGoBack()) {
            myWebView.goBack()
        } else {
            super.onBackPressed()
        }
    }
}