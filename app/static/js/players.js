$('document').ready(function() {
    'use strict';

    var NOTE_COLUMN_INDEX = 4;
    var OPERATIONS_COLUMN_INDEX = NOTE_COLUMN_INDEX + 1;
    var editedRow = null;

    function updateNote($value, $edit, $update, $cancel) {
        var player = $value.data('username'),
            note = $edit.find('input').val();
        $.ajax({
            method: 'PUT',
            url: '/players/note/' + player,
            contentType: 'application/json',
            data: JSON.stringify(note)
        }).done(function() {
            $value.text(note);
            $('#players').trigger('update');
            cancelNoteEditing($value, $edit, $update, $cancel);
        }).fail(function() {
            console.log('fail');
        });
    }

    function cancelNoteEditing($value, $edit, $update, $cancel) {
        $value.show();
        $edit.hide();
        $update.hide();
        $cancel.hide();
        editedRow = null;
    }

    function beginNoteEditing($value, $edit, $update, $cancel) {
        if (editedRow) {
            cancelNoteEditing(editedRow.value, editedRow.edit, editedRow.update, editedRow.cancel);
        }
        $value.hide();
        $edit.show();
        $edit.find('input').text($value.text()).focus();
        $update.show();
        $cancel.show();
        editedRow = { value: $value, edit: $edit, update: $update, cancel: $cancel };
    }

    function handleEditKeys($value, $edit, $update, $cancel, e) {
        if (e.keyCode == 27) {
            cancelNoteEditing($value, $edit, $update, $cancel);
        }
        if (e.keyCode == 13) {
            updateNote($value, $edit, $update, $cancel);
        }
    }

    function noteInit() {
        $('#players > tbody > tr').each(function() {
            var $cells = $(this).children();
            var $value = $cells.eq(NOTE_COLUMN_INDEX).find('.note-value'),
                $edit = $cells.eq(NOTE_COLUMN_INDEX).find('.note-edit'),
                $update = $cells.eq(OPERATIONS_COLUMN_INDEX).find('.update'),
                $cancel = $cells.eq(OPERATIONS_COLUMN_INDEX).find('.cancel');
            $value.click(beginNoteEditing.bind(null, $value, $edit, $update, $cancel));
            $update.click(updateNote.bind(null, $value, $edit, $update, $cancel));
            $cancel.click(cancelNoteEditing.bind(null, $value, $edit, $update, $cancel));
            $edit.find('input').keyup(handleEditKeys.bind(null, $value, $edit, $update, $cancel));
        });
    }

    function initTableSorter() {
        $('#players').tablesorter({
            cssAsc: 'asc',
            cssDesc: 'desc',
            cssHeader: 'no-sort'
        });
    }

    function init() {
        noteInit();
        initTableSorter();
    }

    init();
});