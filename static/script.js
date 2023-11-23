var minimum = 0;
function getFormData($form) {
  var unindexed_array = $form.serializeArray();
  var indexed_array = {};

  $.map(unindexed_array, function (n, i) {
    indexed_array[n['name']] = n['value'];
  });

  return indexed_array;
}

$('form').submit(function (event) {
  event.preventDefault();
  let formData = getFormData($("form"));
  console.log(formData);
  //check that money is positive
  if (formData['money'] < minimum) {
    $('#resultMessage').html("You cannot add a negative amount of money.");
    $('#resultModal').modal('show');
    return;
  }
  $.ajax({
    url: $(this).attr('action'),
    type: "POST",
    dataType: 'json',
    data: JSON.stringify(formData),
    contentType: 'application/json;charset=UTF-8',
    success: function (data) {
      $('#resultMessage').html(data['message'] + "</br> The new balance is <b>" + data['money'] + "€</b>.");
      $('#resultModal').modal('show');
    }
  });
});