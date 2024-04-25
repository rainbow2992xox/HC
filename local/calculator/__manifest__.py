{
    'name': 'hc',
    'version': '1.0.0',
    'depends': ['base'],
    'data': [
        'views/calculator.xml',
        'views/doctor.xml',
        'views/menu.xml',
        'views/table_temp.xml',
    ],
    'assets': {
        'web.assets_backend': [
            '/calculator/static/src/css/style.scss',
            '/calculator/static/src/js/style.js',
            '/calculator/static/src/js/table.js'
            '/calculator/static/src/img/line.png'
        ],
        'web.assets_qweb': [
        ],

    }
}
