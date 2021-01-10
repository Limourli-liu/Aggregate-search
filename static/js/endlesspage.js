/*endlesspage.js*/
var pid = 0; //设置当前页数，全局变量
var lock = false //互斥锁
$(function () {
    function getData() {
        if (lock){return}
        lock = true
        $.getJSON($SCRIPT_ROOT + "/api/info", {pid: pid}, function (data, status) {
            if (status == "success" && data.length > 0){
                pid++; //页码自动增加，保证下次调用时为新的一页。
                lock = false
                insertDiv(data);
            }
            else{
                lock = false
            }
        });
      }
    //生成数据html,append到div中
    function insertDiv(json) {
        var $content = $(".site-content");
        var html = '';
        for (var i = 0; i < json.length; i++) {
            html += '<article class="post-item">';
            html += '<div class="post-title"><a href="' + json[i][3] + '" target="_blank">' + json[i][0] + '</a></div>';
            html += '<div class="post-text">' + json[i][1] + '</div>';
            html += '<div class="post-info">' + json[i][2] + '</div>';
            html += '</article>';
        }
        $content.append(html);
    }
    //初始化加载第一页数据
    getData();
    //==============核心代码=============
    function getScrollTop() {  
        var scrollTop = document.documentElement.scrollTop || window.pageYOffset || document.body.scrollTop;  
        return scrollTop;
    } 
    var winH = $(window).height(); //页面可视区域高度
    var scrollHandler = function () {
        var pageH = $(document).height();
        var scrollT = getScrollTop(); //滚动条top
        var aa = (pageH - winH - scrollT) / winH;
        if (aa < 0.02) {//0.02是个参数
            getData();
        }
    }
    //定义鼠标滚动事件
    $(window).scroll(scrollHandler);
    //==============核心代码=============
});

