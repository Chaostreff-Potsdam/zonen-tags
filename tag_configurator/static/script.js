$('#upload_image_form').on('keyup keypress', function (e) {
    var keyCode = e.keyCode || e.which;
    if (keyCode === 13) {
        e.preventDefault();
        $("#upload_image_button").click();
        return false;
    }
});
$('#form').on('keyup keypress', function (e) {
    var keyCode = e.keyCode || e.which;
    if (keyCode === 13) {
        e.preventDefault();
        $("#upload_button").click();
        return false;
    }
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

$("#dectIcon").click(function () {
    $("#iconSelectionModal img").each(function () {
        $(this).click(function () {
            $("#iconSelectionModal").modal("hide");
            $("#dectIcon").attr("src", $(this).attr("src"));
            let icon = $(this).attr("src").split("/");
            console.log(icon);
            console.log(icon[icon.length - 1]);
            $("input[name='third_line_icon1']").attr("value", icon[icon.length - 1]);
        });
    });
    $("#iconSelectionModal").modal("show");
});

