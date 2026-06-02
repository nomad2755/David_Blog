/**
 * 简历工作经历 JSON 辅助脚本
 * 在 admin 后台为 resume_work_experience 字段添加"填入示例"按钮
 */
(function() {
    'use strict';

    var SAMPLE_JSON = JSON.stringify([
        {
            "company": "XX科技有限公司",
            "position": "高级Python工程师",
            "period": "2022.06 - 至今",
            "projects": [
                {
                    "name": "智能客服系统",
                    "desc": "负责后端架构设计与开发，使用Django+Redis+Celery实现异步消息队列，日均处理10万+对话",
                    "tech": "Python, Django, Redis, Celery, MySQL"
                },
                {
                    "name": "数据中台建设",
                    "desc": "搭建统一数据采集与分析平台，支持多数据源接入和实时分析",
                    "tech": "Python, FastAPI, ClickHouse, Kafka"
                }
            ]
        },
        {
            "company": "YY互联网公司",
            "position": "Python开发工程师",
            "period": "2019.07 - 2022.05",
            "projects": [
                {
                    "name": "电商平台后端",
                    "desc": "负责商品、订单、支付模块的开发与维护，支撑日均百万级交易",
                    "tech": "Python, Flask, SQLAlchemy, RabbitMQ"
                }
            ]
        }
    ], null, 2);

    function init() {
        var textarea = document.getElementById('id_resume_work_experience');
        if (!textarea) return;

        // 创建按钮容器
        var btnGroup = document.createElement('div');
        btnGroup.style.cssText = 'margin: 6px 0; display: flex; gap: 8px; flex-wrap: wrap;';

        // "填入示例" 按钮
        var sampleBtn = document.createElement('button');
        sampleBtn.type = 'button';
        sampleBtn.textContent = '📋 填入示例数据';
        sampleBtn.className = 'button';
        sampleBtn.style.cssText = 'padding: 4px 12px; font-size: 12px; cursor: pointer;';
        sampleBtn.onclick = function() {
            if (textarea.value.trim() === '' || confirm('当前已有内容，确认替换为示例数据？')) {
                textarea.value = SAMPLE_JSON;
                textarea.dispatchEvent(new Event('input', { bubbles: true }));
            }
        };

        // "格式化" 按钮
        var formatBtn = document.createElement('button');
        formatBtn.type = 'button';
        formatBtn.textContent = '🔧 格式化JSON';
        formatBtn.className = 'button';
        formatBtn.style.cssText = 'padding: 4px 12px; font-size: 12px; cursor: pointer;';
        formatBtn.onclick = function() {
            var val = textarea.value.trim();
            if (!val) return;
            try {
                var obj = JSON.parse(val);
                textarea.value = JSON.stringify(obj, null, 2);
                textarea.dispatchEvent(new Event('input', { bubbles: true }));
            } catch (e) {
                alert('JSON格式错误: ' + e.message);
            }
        };

        // "验证" 按钮
        var validateBtn = document.createElement('button');
        validateBtn.type = 'button';
        validateBtn.textContent = '✅ 验证JSON';
        validateBtn.className = 'button';
        validateBtn.style.cssText = 'padding: 4px 12px; font-size: 12px; cursor: pointer;';
        validateBtn.onclick = function() {
            var val = textarea.value.trim();
            if (!val) {
                alert('字段为空，无需验证');
                return;
            }
            try {
                var data = JSON.parse(val);
                if (!Array.isArray(data)) {
                    alert('❌ 顶层必须是数组');
                    return;
                }
                for (var i = 0; i < data.length; i++) {
                    var item = data[i];
                    if (!item.company || !item.position || !item.period) {
                        alert('❌ 第' + (i + 1) + '项缺少必填字段 (company/position/period)');
                        return;
                    }
                    if (item.projects && !Array.isArray(item.projects)) {
                        alert('❌ 第' + (i + 1) + '项的 projects 必须是数组');
                        return;
                    }
                }
                alert('✅ JSON格式正确！共 ' + data.length + ' 条工作经历');
            } catch (e) {
                alert('❌ JSON格式错误: ' + e.message);
            }
        };

        btnGroup.appendChild(sampleBtn);
        btnGroup.appendChild(formatBtn);
        btnGroup.appendChild(validateBtn);

        textarea.parentNode.insertBefore(btnGroup, textarea);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
