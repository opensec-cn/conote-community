require.config({
    paths: {
        'vs': 'https://cdn.jsdelivr.net/npm/monaco-editor@0.13.1/min/vs'
    }
});
require(['vs/editor/editor.main'], () => {
    $("#btn-panel").show().insertBefore($("#editor"));
    const editor = monaco.editor.create(document.getElementById('editor'), {
        value: $("#id_payload").val(),
        language: 'javascript',
        wordWrap: 'on'
    });

    const clipboard = new ClipboardJS('.clip-btn');

    $('#minify').on('click', () => {
        const { code, error } = uglify.minify(editor.getValue());
        editor.setValue(code)
    });

    $('#beautify').on('click', () => {
        const code = beautify(editor.getValue());
        editor.setValue(code)
    });

    $('#project-submit').on('click', () => {
        const code = editor.getValue();
        $("#id_payload").val(code);
        $('#project-form').submit();
    });

    $('#payload-template').chosen().change(() => {
        const { code, error } = uglify.minify($('#payload-template').val());
        editor.trigger('keyboard', 'type', {text: code});
    });

})