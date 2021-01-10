/*endlesspage.js*/
var gPageSize = 10;
var i = 1; //设置当前页数，全局变量
$(function () {
  //根据页数读取数据
  function getData(pagenumber) {
    i++; //页码自动增加，保证下次调用时为新的一页。
    $.get("/ajax/Handler.ashx", { pagesize: gPageSize, pagenumber: pagenumber }, function (data) {
      if (data.length > 0) {
        var jsonObj = JSON.parse(data);
        insertDiv(jsonObj);
      }
    });
    $.ajax({
      type: "post",
      url: "/ajax/Handler.ashx",
      data: { pagesize: gPageSize, pagenumber: pagenumber },
      dataType: "json",
      success: function (data) {
        $(".loaddiv").hide();
        if (data.length > 0) {
          var jsonObj = JSON.parse(data);
          insertDiv(jsonObj);
        }
      },
      beforeSend: function () {
        $(".loaddiv").show();
      },
      error: function () {
        $(".loaddiv").hide();
      }
    });
  }
  //初始化加载第一页数据
  getData(1);
  //生成数据html,append到div中
  function insertDiv(json) {
    var $mainDiv = $(".mainDiv");
    var html = '';
    for (var i = 0; i < json.length; i++) {
      html += '<div class="item">';
      html += ' <div class="title">' + json[i].rowId + '  ' + json[i].D_Name + '</div>';
      html += ' <div class="content">' + json[i].D_Name + '  ' + json[i].D_Password + '</div>';
      html += '</div>';
    }
    $mainDiv.append(html);
  }
  //==============核心代码=============
  var winH = $(window).height(); //页面可视区域高度
  var scrollHandler = function () {
    var pageH = $(document.body).height();
    var scrollT = $(window).scrollTop(); //滚动条top
    var aa = (pageH - winH - scrollT) / winH;
    if (aa < 0.02) {//0.02是个参数
      if (i % 10 === 0) {//每10页做一次停顿！
        getData(i);
        $(window).unbind('scroll');
        $("#btn_Page").show();
      } else {
        getData(i);
        $("#btn_Page").hide();
      }
    }
  }
  //定义鼠标滚动事件
  $(window).scroll(scrollHandler);
  //==============核心代码=============
  //继续加载按钮事件
  $("#btn_Page").click(function () {
    getData(i);
    $(window).scroll(scrollHandler);
  });
});