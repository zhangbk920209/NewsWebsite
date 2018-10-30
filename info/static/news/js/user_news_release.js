function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

// function getValue() {
//     var r = $('#rich_content').value()
//     return r
// }

$(function () {

    $(".release_form").submit(function (e) {
        e.preventDefault()
        //  发布完毕之后需要选中我的发布新闻
        // // 选中索引为6的左边单菜单
        // window.parent.fnChangeMenu(6)
        // // 滚动到顶部
        // window.parent.scrollTo(0, 0)
        // 发布完毕之后需要选中我的发布新闻
        // params ={
        //     'content': $('#rich_content').val()
        //     'title':
        // }
        $(this).ajax({
            beforeSubmit: function (request) {
                for(var i=0; i<request.length; i++){
                    var item = request[i];
                    if(item['name'] == 'content'){
                        item['value'] = tinyMCE.activeEditor.getContent()
                    }
                }
            },
            url: "/user_news_release",
            type: "POST",
            headers: {
                "X-CSRFToken": getCookie('csrf_token')
            },
            success: function (resp) {
                if (resp.errno == "0") {
                    // 选中索引为6的左边菜单
                    window.parent.fnChangeMenu(6)
                    // 滚动到顶部
                    window.parent.scrollTo(0, 0)
                }else {
                    alert(resp.errmsg)
                }
            }
        })

    })
})