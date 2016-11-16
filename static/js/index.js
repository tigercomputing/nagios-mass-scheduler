/**
 This file is part of mass-scheduler.

mass-scheduler is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version.

mass-scheduler is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with
mass-scheduler.  If not, see <http://www.gnu.org/licenses/>.

Copyright {c} 2016 Tiger Computing Ltd
/**


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
    const inputs = [].slice.call(document.getElementsByTagName('input'));
    const checkboxes = inputs.filter(i => i.type === 'checkbox');
    const filledIn = checkboxes.map(box => box.checked).some(bool => bool);

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


$(function () {

    // Store mouse state
    var isMouseDown = false;

    /**
     * Clicking a table row will toggle checkbox for that row, dragging whilst
     * holding down the mouse will highlight multiple rows
     */
    $('table tr')
        .mousedown(function () {
            isMouseDown = true;
            $(':checkbox', this).trigger('click');
            return false; // prevent text selection
        })
        .mouseover(function () {
            if (isMouseDown) {
                $(':checkbox', this).trigger('click');
            }
        });

    /**
     * Resets the mousedown status flag
     */
    $(document) .mouseup(function () {
        isMouseDown = false;
    });

});


/**
 * Code runs on initial page load
 */
$(document).ready(function() {

    // Prevent accidental form submission on Enter press when searching
    $('input[type=search]').keydown(function(event){
        if(event.keyCode === 13) {
            event.preventDefault();
            return false;
        }
    });

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
    onSelect: () => togglebutton(),
    dateFormat: 'dd-mm-yyyy',
    timeFormat: 'hh:ii',
});


/**
 * Sets the time input field to 17:00 today
 */
$('#setTime').on('click', function() {
    var datepicker = $('#timeInput').datepicker().data('datepicker');
    var today = new Date();
    today.setHours(17);
    today.setMinutes(0);
    today.setSeconds(0);
    datepicker.selectDate(today);
    togglebutton();
});
