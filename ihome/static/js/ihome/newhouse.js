function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

$(document).ready(function(){
    // 向后端获取城区信息
    $.get("/api/v1.0/areas", function (resp) {

        if (resp.errno == 0) {

            var areas = resp.data;
            // for (i=0; i<areas.length; i++) {
            //     console.log('1');
            //     $("#area-id").append('<option value="'+ area.aid +'">'+ area.aname +'</option>');
            // }
            // $.each(areas,function (i,area) {
            //     $("#area-id").append('<option value="'+ area.aid +'">'+ area.aname +'</option>');
            // })

            // 使用js模板
            var html = template('areas-tmpl',{areas:areas});
            $('#area-id').html(html)


        } else {
            alert(resp.msg);
        }

    }, "json");
});