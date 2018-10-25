function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

$(function () {

    $(".base_info").submit(function (e) {
        e.preventDefault()

        var signature = $("#signature").val()
        var nick_name = $("#nick_name").val()
        var gender = $(".gender").val()

        if (!nick_name) {
            alert('请输入昵称')
            return
        }
        if (!gender) {
            alert('请选择性别')
        }

        // 修改用户信息接口
        var params = {
            nick_name:nick_name,
            signature:signature,
            gender:gender
        }
        $.ajax({
            url:'/base_info',
            type:'post',
            data:JSON.stringify(params),
            contentType:'application/json',
            headers:{
                'X-CSRFToken':getCookie('csrf_token')
            },
            success:function (resp) {
                if (resp.errno == 0){
                    // 更新父窗口内容
                    $('.user_center_name', parent.document).html(params['nick_name'])
                    $('#nick_name', parent.document).html(params['nick_name'])
                    $('.input_sub').blur()
                }else {
                    alert(resp.errmsg)
                }
            }
        })
    })
})