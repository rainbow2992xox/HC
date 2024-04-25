odoo.define('hc.custom_styles', [], function (require) {
    "use strict";
    $(document).ready(async function () {
        const Response = await fetch('/check_user', {
            method: 'POST', // 或者 'GET', 'PUT', 'DELETE' 等
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({})
        });

        var styleTag = document.createElement('style');
        styleTag.type = 'text/css';

        // 添加样式规则
        styleTag.innerHTML = `
           .o_main_navbar {
              background-color: #71639e !important;
              border-bottom: 0px;
              display: none;
        }
           .o_control_panel {
                  position:absolute;
        }
        `;
        const res = await Response.json();
        console.log(res)
        if (res.result) {
            console.log("in")
            document.head.appendChild(styleTag);
        } else {
            console.log("out")
        }


    });

});
