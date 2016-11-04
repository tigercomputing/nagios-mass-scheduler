/**
 * Changes the style and text of the form submission button depending on the
 * current state of the `timeInput` field
 */
function togglebutton() {
    if ($('#timeInput').val() === '') {
        $('#submitButton').removeClass('btn-primary').addClass('btn-success');
        $('#submitButton').text('Acknowledge');
    } else {
        $('#submitButton').removeClass('btn-success').addClass('btn-primary');
        $('#submitButton').text('Schedule Downtime');
    }
}


/**
 * Performs basic validation and prevents unnecessary post request if form data
 * is missing
 */
$('.form').submit(f => {
    // Find all the inputs on the page
    var inputs = [].slice.call(document.getElementsByTagName('input'));
    var checkboxes = inputs.filter(i => i.type === 'checkbox');
    var filledIn = checkboxes.map(box => box.checked).some(bool => bool);

    if (!filledIn) {
        f.preventDefault();
        $('#errorContent').text('Select services to apply action to!');
        $('#errorBox').removeClass('hidden');
        return;
    }

    if($('#messageInput').val() === '' || $('#userInput').val() === '') {
        f.preventDefault();
        $('#errorContent').text('Please provide a username and message');
        $('#errorBox').removeClass('hidden');
        return;
    }

    if($('#timeInput').val() !== '') {
        var datepicker = $('#timeInput').datepicker().data('datepicker');
        selectedDate = datepicker.selectedDates[0];
        if(selectedDate <= new Date()) {
            f.preventDefault();
            $('#errorContent').text('Select a future time to avoid nagios confusion');
            $('#errorBox').removeClass('hidden');
            return;

        }
    }

});


/**
 * Register callback functions to fire off on events which effect the form
 */
$('#timeInput').bind('keyup change', () => togglebutton());

$('#clearButton').on('click', function() {
    $('#timeInput').val('');
    togglebutton();
});


/**
 * Clicking the toggleAll button will toggle all checkboxes
 */
$('#toggleAll').click(function() {
    $('table input:checkbox').each(function() {
        $(this).prop('checked', !$(this).prop('checked'));
    });
});


/**
 * Clicking a table row will toggle checkbox for that row
 */
$('table tr').click(function(event) {
    if (event.target.type !== 'checkbox') {
        $(':checkbox', this).trigger('click');
    }
});


/**
 * Code runs on initial page load
 */
$(document).ready(function() {

    // Set the current button status
    togglebutton();

    // Configure list.js attributes
    var options = {
        valueNames: ['host_name', 'service_description', 'plugin_output']
    };
    new List('services-list', options);

});


/**
 * Datepicker configuration
 */
$('#timeInput').data({
    minutesStep: 5,
    timepicker: true,
    minDate: new Date(),
    dateFormat: 'dd/mm/yyyy',
});



/**
 * Sets the time input field to the current time
 */
$('#setTime').on('click', function() {
    var datepicker = $('#timeInput').datepicker().data('datepicker');
    var currentTime = new Date();
    currentTime.setMinutes(currentTime.getMinutes() + 5);
    datepicker.selectDate(currentTime);
    togglebutton();
});
