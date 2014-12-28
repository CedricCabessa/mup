import os

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtWebKit import *

import converters

from converterthread import ConverterThread


class WebPage(QWebPage):
    def javaScriptConsoleMessage(self, msg, lineNumber, sourceID):
        print "JsConsole(%s:%d): %s" % (sourceID, lineNumber, msg)


class View(QWidget):
    internalUrlClicked = pyqtSignal(QUrl)
    loadRequested = pyqtSignal(QString)

    def __init__(self, dataDir, parent=None):
        QWidget.__init__(self, parent)
        self.dataDir = dataDir
        self._thread = ConverterThread()
        self._thread.done.connect(self._setHtml)

        self.setupView()

        self.setupLinkLabel()

        layout = QHBoxLayout(self)
        layout.setMargin(0)
        layout.addWidget(self.view)

        self._lastScrollPos = None

    def setupView(self):
        self.view = QWebView(self)
        page = WebPage()
        page.setLinkDelegationPolicy(QWebPage.DelegateAllLinks)
        page.linkClicked.connect(self._openUrl)
        page.linkHovered.connect(self.showHoveredLink)
        self.view.setPage(page)

    def setupLinkLabel(self):
        self.linkLabel = QLabel(self.view)
        self.linkLabel.setStyleSheet("""
        background-color: #abc;
        color: #123;
        padding: 3px;
        border-bottom-right-radius: 3px;
        border-right: 1px solid #bce;
        border-bottom: 1px solid #bce;
        """)
        self.linkLabel.hide()
        self.linkLabelHideTimer = QTimer(self)
        self.linkLabelHideTimer.setSingleShot(True)
        self.linkLabelHideTimer.setInterval(250)
        self.linkLabelHideTimer.timeout.connect(self.linkLabel.hide)

    def load(self, filename, converter):
        self._thread.setFilename(filename)
        self._thread.setConverter(converter)
        self.reload()

    def reload(self):
        self._thread.start()

    def _setHtml(self, html):
        frame = self.view.page().currentFrame()
        self._lastScrollPos = frame.scrollPosition()

        filename = unicode(self._thread.filename())
        baseUrl = QUrl.fromLocalFile(os.path.dirname(filename) + "/")
        self.view.loadFinished.connect(self._onLoadFinished)
        self.view.setHtml(html, baseUrl)

    def setConverter(self, converter):
        self._thread.setConverter(converter)
        self.reload()

    def _onLoadFinished(self):
        if self._lastScrollPos is not None:
            frame = self.view.page().currentFrame()
            frame.setScrollPosition(self._lastScrollPos)
            self._lastScrollPos = None
            self.view.loadFinished.disconnect(self._onLoadFinished)

    def _openUrl(self, url):
        if url.scheme() == "internal":
            self.internalUrlClicked.emit(url)
        if url.scheme() in ("file", "") and \
                converters.findConverters(unicode(url.path())):
            self.loadRequested.emit(url.path())
        else:
            QDesktopServices.openUrl(url)

    def showHoveredLink(self, link, title, textContent):
        if link.isEmpty():
            self.linkLabelHideTimer.start()
            return

        self.linkLabelHideTimer.stop()
        text = link
        text.replace("file:///", "/")
        self.linkLabel.setText(text)
        self.linkLabel.adjustSize()

        self.linkLabel.show()
