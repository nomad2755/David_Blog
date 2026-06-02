/**
 * mdeditor 粘贴图片支持
 * 
 * 监听编辑器中的 paste 事件，当粘贴内容包含图片时，
 * 自动上传图片并插入 Markdown 图片语法。
 */
(function() {
    'use strict';

    // 存储 editor.md 实例的映射表 (wrapperId -> editor instance)
    var editorInstances = {};

    /**
     * 拦截 editormd() 调用，保存实例引用
     */
    function hookEditormd() {
        if (typeof editormd === 'undefined') return;

        var originalEditormd = editormd;
        var wrappedFn = function() {
            var result = originalEditormd.apply(this, arguments);
            if (result && result.id) {
                editorInstances[result.id] = result;
            }
            return result;
        };
        // 复制所有属性
        for (var key in originalEditormd) {
            if (originalEditormd.hasOwnProperty(key)) {
                wrappedFn[key] = originalEditormd[key];
            }
        }
        window.editormd = wrappedFn;
    }

    function getCookie(name) {
        var cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    /**
     * 上传图片文件到服务器
     */
    function uploadImage(file) {
        var formData = new FormData();
        formData.append('editormd-image-file', file);

        return fetch('/mdeditor/uploads/', {
            method: 'POST',
            body: formData,
            credentials: 'same-origin'
        }).then(function(response) {
            return response.json();
        });
    }

    /**
     * 在 CodeMirror 编辑器中插入文本
     */
    function insertMarkdown(wrapper, text) {
        // 方法1: 通过保存的 editor.md 实例
        var wrapperId = wrapper.id;
        if (editorInstances[wrapperId] && editorInstances[wrapperId].cm) {
            editorInstances[wrapperId].cm.replaceSelection(text);
            editorInstances[wrapperId].cm.focus();
            return;
        }

        // 方法2: 通过 DOM 查找 CodeMirror 实例
        var cmElement = wrapper.querySelector('.CodeMirror');
        if (cmElement && cmElement.CodeMirror) {
            cmElement.CodeMirror.replaceSelection(text);
            cmElement.CodeMirror.focus();
            return;
        }

        // 方法3: 备用 - 操作 textarea
        var textarea = wrapper.querySelector('textarea');
        if (textarea) {
            var start = textarea.selectionStart;
            var end = textarea.selectionEnd;
            var value = textarea.value;
            textarea.value = value.substring(0, start) + text + value.substring(end);
            textarea.selectionStart = textarea.selectionEnd = start + text.length;
            textarea.focus();
            textarea.dispatchEvent(new Event('input', { bubbles: true }));
            textarea.dispatchEvent(new Event('change', { bubbles: true }));
        }
    }

    /**
     * 查找编辑器容器
     */
    function findEditorWrapper(element) {
        // 向上查找 wmd-wrapper 或 editormd 容器
        var el = element;
        while (el) {
            if (el.classList) {
                if (el.classList.contains('wmd-wrapper') || el.classList.contains('editormd')) {
                    return el;
                }
            }
            if (el.id && el.id.indexOf('-wmd-wrapper') !== -1) {
                return el;
            }
            el = el.parentElement;
        }
        return null;
    }

    /**
     * 处理粘贴事件
     */
    function handlePaste(e) {
        var clipboardData = e.clipboardData || window.clipboardData;
        if (!clipboardData) return;

        var items = clipboardData.items;
        if (!items) return;

        for (var i = 0; i < items.length; i++) {
            if (items[i].type.indexOf('image') !== -1) {
                e.preventDefault();
                e.stopPropagation();

                var file = items[i].getAsFile();
                if (!file) continue;

                var wrapper = findEditorWrapper(e.target);
                if (!wrapper) return;

                // 上传图片并插入
                uploadImage(file).then(function(data) {
                    if (data.success === 1) {
                        var imageMarkdown = '![图片](' + data.url + ')';
                        insertMarkdown(wrapper, imageMarkdown);
                    } else {
                        alert('图片上传失败: ' + (data.message || '未知错误'));
                    }
                }).catch(function(err) {
                    console.error('图片上传错误:', err);
                    alert('图片上传失败，请重试');
                });

                break;
            }
        }
    }

    /**
     * 处理拖拽事件
     */
    function handleDrop(e) {
        var files = e.dataTransfer && e.dataTransfer.files;
        if (!files || files.length === 0) return;

        for (var i = 0; i < files.length; i++) {
            if (files[i].type.indexOf('image') !== -1) {
                var wrapper = findEditorWrapper(e.target);
                if (!wrapper) return;

                e.preventDefault();
                e.stopPropagation();

                var file = files[i];
                uploadImage(file).then(function(data) {
                    if (data.success === 1) {
                        var imageMarkdown = '![图片](' + data.url + ')';
                        insertMarkdown(wrapper, imageMarkdown);
                    } else {
                        alert('图片上传失败: ' + (data.message || '未知错误'));
                    }
                }).catch(function(err) {
                    console.error('图片上传错误:', err);
                    alert('图片上传失败，请重试');
                });

                break;
            }
        }
    }

    /**
     * 初始化
     */
    function init() {
        // 先拦截 editormd 函数以保存实例
        hookEditormd();

        // 使用事件委托监听 paste 和 drop
        document.addEventListener('paste', handlePaste, true);
        document.addEventListener('drop', handleDrop, true);

        // 阻止编辑器区域的默认拖拽行为
        document.addEventListener('dragover', function(e) {
            if (findEditorWrapper(e.target)) {
                e.preventDefault();
            }
        });
    }

    // 页面加载后初始化
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();
