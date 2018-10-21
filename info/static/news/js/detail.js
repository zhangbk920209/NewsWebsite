function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}
function add_reply() {
    $(this).parent().show()
}

$(function(){

    // 打开登录框
    $('.comment_form_logout').click(function () {
        $('.login_form_con').show();
    })
    // // 弹出回复框
    // $('.comment_reply').click(function () {
    //     $('.reply_form').show()
    // })
    // 收藏
    $(".collection").click(function () {
        var news_id = $('.collection').attr('news_id')
        var action = 'collect'
        var params = {
            news_id:news_id,
            action:action
        }
        $.ajax({
            url:'/news_collection',
            type:'post',
            data:JSON.stringify(params),
            contentType:'application/json',
            headers:{
                'X-CSRFToken':getCookie('csrf_token')
            },
            success:function (resp) {
                if(resp.errno == 0){
                    $('.collection').hide()
                    $('.collected').show()
                }else if (resp.errno == 4101){
                    alert('请先登陆')
                    $('.login_form_con').show();
                }else {
                    alert('收藏失败')
                }
            }
        })
    })

    // 取消收藏
    $(".collected").click(function () {
        var news_id = $('.collected').attr('news_id')
        var action = 'cancel_collect'
        var params = {
            news_id:news_id,
            action:action
        }
        $.ajax({
            url:'/news_collection',
            type:'post',
            data:JSON.stringify(params),
            contentType:'application/json',
            headers:{
                'X-CSRFToken':getCookie('csrf_token')
            },
            success:function (resp) {
                if(resp.errno == 0){
                    $('.collection').show()
                    $('.collected').hide()
                }else {
                    alert('取消收藏')
                }
            }
        })
     
    })

        // 评论提交
    $(".comment_form").submit(function (e) {
        e.preventDefault();
        var comment_content = $('.comment_input').val()
        var news_id = $('.collection').attr('news_id')
        var parent_id = $('.user_name2').attr('parent_id')
        if(!comment_content){
            alert('请输入评论')
            return
        }
        var params = {
            comment:comment_content,
            news_id:news_id,
            parent_id:parent_id
        }
        $.ajax({
            url:'/comment',
            type:'post',
            data:JSON.stringify(params),
            headers:{
                'X-CSRFToken':getCookie('csrf_token')
            },
            contentType:'application/json',
            success:function (resp) {
                if(resp.errno == 0){
                    location.reload()
                }else {
                    alert(resp.errmsg)
                }
            }

        })

    })

    $('.comment_list_con').delegate('a,input','click',function(){

        var sHandler = $(this).prop('class');

        if(sHandler.indexOf('comment_reply')>=0)
        {
            $(this).next().toggle();
        }

        if(sHandler.indexOf('reply_cancel')>=0)
        {
            $(this).parent().toggle();
        }

        if(sHandler.indexOf('comment_up')>=0)
        {
            var $this = $(this);
            if(sHandler.indexOf('has_comment_up')>=0)
            {
                // 如果当前该评论已经是点赞状态，再次点击会进行到此代码块内，代表要取消点赞
                $this.removeClass('has_comment_up')
            }else {
                $this.addClass('has_comment_up')
            }
        }

        if(sHandler.indexOf('reply_sub')>=0)
        {
            alert('回复评论')
        }
    })

        // 关注当前新闻作者
    $(".focus").click(function () {

    })

    // 取消关注当前新闻作者
    $(".focused").click(function () {

    })
})