const HyperMD = require('hypermd')
const CodeMirror = require('codemirror')
import ace from 'ace-builds'
import 'ace-builds/src-noconflict/mode-html'
import 'ace-builds/src-noconflict/ext-language_tools'

const container = document.getElementById('id_content')
const js_config = JSON.parse(document.getElementById('js_config').textContent);
const key = `content_save_${js_config.action}`
let editor;

if(js_config.action === 'article') {
    editor = HyperMD.fromTextArea(container)
} else if (js_config.action === 'text') {
    const textarea = $("#id_content");
    let editDiv = $('<div>', {
        width: '100%'
    }).insertBefore(textarea)
    textarea.hide()

    const CDN = 'https://cdn.jsdelivr.net/npm/ace-builds@1.3.3/src-min-noconflict'
    ace.config.set('basePath', CDN)
    ace.config.set('modePath', CDN)
    ace.config.set('themePath', CDN)
    ace.config.set('workerPath', CDN)
    editor = ace.edit(editDiv[0], {
        mode: "ace/mode/html",
        selectionStyle: "text",
        enableBasicAutocompletion: true,
        enableSnippets: true,
        enableLiveAutocompletion: false,
        autoScrollEditorIntoView: true,
        maxLines: 50,
        minLines: 10,
        wrap: true,
        tabSize: 2
    })
    editor.session.setValue(textarea.val())

    textarea.closest('form').on('submit', () => {
        textarea.val(editor.getValue())
    })
} else if (js_config.action === 'code') {
    editor = CodeMirror.fromTextArea(container, {
        lineNumbers: true,
        lineWrapping: true,
        indentUnit: 4,
        lineSeparator: '\n',
    })
}

if (editor) {
    if (key in window.localStorage && !editor.getValue()) {
        editor.setValue(window.localStorage.getItem(key))
    }
    editor.on("change", (e, obj) => {
        window.localStorage.setItem(key, editor.getValue());
    })
}

$('.filestyle').filestyle();
$(".generate").on('click', () => {
      let text = ""
      const possible = "abcdef0123456789"

      for (let i = 0; i < 6; i++)
        text += possible.charAt(Math.floor(Math.random() * possible.length))

      $("#id_filename").val(text)
})

const types = [
      {
        "value": "text/plain"
      },
      {
        "value": "audio/aac"
      },
      {
        "value": "application/x-abiword"
      },
      {
        "value": "application/octet-stream"
      },
      {
        "value": "video/x-msvideo"
      },
      {
        "value": "application/vnd.amazon.ebook"
      },
      {
        "value": "application/x-bzip"
      },
      {
        "value": "application/x-bzip2"
      },
      {
        "value": "application/x-csh"
      },
      {
        "value": "text/css"
      },
      {
        "value": "text/csv"
      },
      {
        "value": "application/msword"
      },
      {
        "value": "application/vnd.ms-fontobject"
      },
      {
        "value": "application/epub+zip"
      },
      {
        "value": "image/gif"
      },
      {
        "value": "text/html"
      },
      {
        "value": "image/x-icon"
      },
      {
        "value": "text/calendar"
      },
      {
        "value": "application/java-archive"
      },
      {
        "value": "image/jpeg"
      },
      {
        "value": "application/javascript"
      },
      {
        "value": "application/json"
      },
      {
        "value": "audio/midi"
      },
      {
        "value": "video/mpeg"
      },
      {
        "value": "application/vnd.apple.installer+xml"
      },
      {
        "value": "application/vnd.oasis.opendocument.presentation"
      },
      {
        "value": "application/vnd.oasis.opendocument.spreadsheet"
      },
      {
        "value": "application/vnd.oasis.opendocument.text"
      },
      {
        "value": "audio/ogg"
      },
      {
        "value": "video/ogg"
      },
      {
        "value": "application/ogg"
      },
      {
        "value": "font/otf"
      },
      {
        "value": "image/png"
      },
      {
        "value": "application/pdf"
      },
      {
        "value": "application/vnd.ms-powerpoint"
      },
      {
        "value": "application/x-rar-compressed"
      },
      {
        "value": "application/rtf"
      },
      {
        "value": "application/x-sh"
      },
      {
        "value": "image/svg+xml"
      },
      {
        "value": "application/x-shockwave-flash"
      },
      {
        "value": "application/x-tar"
      },
      {
        "value": "image/tiff"
      },
      {
        "value": "application/typescript"
      },
      {
        "value": "font/ttf"
      },
      {
        "value": "application/vnd.visio"
      },
      {
        "value": "audio/x-wav"
      },
      {
        "value": "audio/webm"
      },
      {
        "value": "video/webm"
      },
      {
        "value": "image/webp"
      },
      {
        "value": "font/woff"
      },
      {
        "value": "font/woff2"
      },
      {
        "value": "application/xhtml+xml"
      },
      {
        "value": "application/vnd.ms-excel"
      },
      {
        "value": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
      },
      {
        "value": "application/xml"
      },
      {
        "value": "application/zip"
      },
      {
        "value": "video/3gpp"
      },
      {
        "value": "audio/3gpp"
      },
      {
        "value": "video/3gpp2"
      },
      {
        "value": "audio/3gpp2"
      },
      {
        "value": "application/x-7z-compressed"
      }
];

$('#id_content_type').autocomplete({
    lookup: types
})
