$('#upload_image_form').on('keyup keypress', function (e) {
    var keyCode = e.keyCode || e.which;
    if (keyCode === 13) {
        e.preventDefault();
        $("#upload_image_button").click();
        return false;
    }
});

$("#save_button").on("click", function () {
    let formData = getFormData($("#form"));
    let download_link = $("#json_download");
    download_link.attr("href", "data:text/json;charset=utf-8," +
     encodeURIComponent(JSON.stringify(formData)));
    download_link.attr("download", formData.nickname + ".json");
    download_link[0].click();
});

$("#load_button").on("click", function () {
   $("#load_modal").modal("show");
});

$('#form').on('keyup keypress', function (e) {
    var keyCode = e.keyCode || e.which;
    if (keyCode === 13) {
        e.preventDefault();
        $("#upload_button").click();
        return false;
    }
});

$("#load_confirm").on("click", function () {
    let file = $("#load_file")[0].files[0];
    let reader = new FileReader();
    reader.onload = function (e) {
        let json = JSON.parse(e.target.result);
        for (let key in json) {
            $("#" + key).val(json[key]);
            if (key.includes("icon")) {
                let image = $("img[icon_slug='" + key + "']");
                console.log(image);
                image.attr("src", "static/icons/" + json[key]);
                image.attr("alt", json[key]);
            }    
        }
    };
    reader.readAsText(file);
});



function getFormData($form) {
    var unindexed_array = $form.serializeArray();
    var indexed_array = {};

    $.map(unindexed_array, function (n, i) {
        indexed_array[n['name']] = n['value'];
    });

    return indexed_array;
}

$("#upload_button").on("click", function () {

    let formData = getFormData($("#form"));
    $.ajax({
        url: "upload",
        type: "POST",

        success: function (data) {
            // $("#resultMessage").text(data["message"]);
            // $("#resultModal").modal("show");
            $("#toastBody").text(data["message"]);
            $("#toast").toast("show");
            $("#example").attr("src", data["file_name"]);
        },
        dataType: 'json',
        data: JSON.stringify(formData),
        contentType: 'application/json;charset=UTF-8',
        // Tell jQuery not to process data or worry about content-type
        // You *must* include these options!
        cache: false,

        processData: false,
    });
});

$("#upload_image_button").on("click", function () {

    $.ajax({
        url: "image_upload",
        type: "POST",
        data: new FormData($("#upload_image_form")[0]),
        success: function (data) {
            $("#toastBody").text(data["message"]);
            $("#toast").toast("show");
            $("#example").attr("src", data["file_name"]);
        },
        processData: false,
        contentType: false,
        cache: false,

    });
});


$("img[icon_slug]").each(function () {
    $(this).click(function () {
        let image = $(this);
        let icon_slug = image.attr("icon_slug");
        $("#iconSelectionModal img").each(function () {
            let selected_icon = $(this);
            selected_icon.off("click");
            selected_icon.click(function () {
                $("#iconSelectionModal").modal("hide");
                image.attr("src", selected_icon.attr("src"));
                let icon_path = $(this).attr("src").split("/");
                let icon_name = icon_path[icon_path.length - 1];
                $("#" + icon_slug).attr("value", icon_name);
            });
        });
        $("#iconSelectionModal").modal("show");
    });
});

