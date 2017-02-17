Array.prototype.contains = function (v) {
    return this.indexOf(v) > -1;
};
running = [];

function extractConfig(programMame) {
    var idStart = programMame + '-';
    var result = {};
    $('input').filter(function (index, element) {
        return element.id.indexOf(idStart) == 0;
    }).each(function (index, element) {
        result[element.id.substring(idStart.length)] =
            element.type == 'checkbox' ? element.checked : element.value;
    });
    return result;
}

function extractConfigValue(programName, valueName) {
    var element = $('input#' + programName + '-' + valueName)[0];
    return element.type == 'checkbox' ? element.checked : element.value;
}

setInterval(updateLog, 1500);

function updateLog() {
    $.ajax({
        async: true,
        method: 'POST',
        url: 'commands/getLog.esp',
        dataType: 'json',
        success: function (output, textStatus, jqXHR) {
            $('pre#log-content')[0].innerHTML = output.logText;
        }
    });
}

function handleStartStopClick(programMame) {
    if (running.contains(programMame)) return;
    running.push(programMame);

    var stateText = $('#program-' + programMame + '-state');
    var startStopButton = $('#program-' + programMame + '-state-switch');
    var successText = $('#program-' + programMame + '-success-text');
    var failText = $('#program-' + programMame + '-fail-text');
    var additionalControlsDiv = $('#program-' + programMame + '-additional-controls');
    startStopButton.disabled = true;
    additionalControlsDiv.hide();

    var config = extractConfig(programMame);

    $.ajax({
        async: true,
        method: 'POST',
        url: 'commands/execute.esp',
        data: {
            name: programMame,
            config: JSON.stringify(config)
        },
        dataType: 'json',
        success: function(output, textStatus, jqXHR) {
            startStopButton[0].innerHTML = output.stateSwitchText;
            stateText[0].innerHTML = output.stateText;
            additionalControlsDiv[0].innerHTML = output.additionalControls;
            if (output.additionalControls.length != 0) additionalControlsDiv.show();
            switch (output.showStatus) {
                case 'success':
                    failText.hide();
                    successText.show();
                    break;
                case 'fail':
                    successText.hide();
                    failText.show();
                    break;
                case 'none':
                default:
                    successText.hide();
                    failText.hide();
            }
        },
        error: function (jqXHR, textStatus, errorThrown) {
            successText.hide();
            failText.show();
        },
        complete: function (jqXHR, status) {
            startStopButton.disabled = false;
            running.splice(running.indexOf(programMame), 1)
        }
    });
}

function handleUpdateConfigClick(programMame) {
    if (running.contains(programMame)) return;
    running.push(programMame);

    var updateButton = $('#program-' + programMame + '-update');
    var successText = $('#program-' + programMame + '-success-text');
    var failText = $('#program-' + programMame + '-fail-text');
    updateButton.disabled = true;

    var config = extractConfig(programMame);

    $.ajax({
        async: true,
        method: 'POST',
        url: 'commands/updateConfig.esp',
        data: {
            name: programMame,
            config: JSON.stringify(config)
        },
        dataType: 'json',
        success: function (output, textStatus, jqXHR) {
            if (output.success == 'true') {
                failText.hide();
                successText.show();
            } else {
                successText.hide();
                failText.show();
            }
        },
        error: function (jqXHR, textStatus, errorThrown) {
            successText.hide();
            failText.show();
        },
        complete: function (jqXHR, status) {
            updateButton.disabled = false;
            running.splice(running.indexOf(programMame), 1)
        }
    });
}

function handleConfigChange(programMame, valueName) {
    var autoUpdateCheckbox = $('input#program-' + programMame + '-config-auto-update');
    if (!autoUpdateCheckbox[0].checked) return;

    if (running.contains(programMame)) return;
    running.push(programMame);

    var updateButton = $('#program-' + programMame + '-update');
    var successText = $('#program-' + programMame + '-success-text');
    var failText = $('#program-' + programMame + '-fail-text');
    updateButton.disabled = true;

    var value = extractConfigValue(programMame, valueName);

    $.ajax({
        async: true,
        method: 'POST',
        url: 'commands/updateConfigValue.esp',
        data: {
            name: programMame,
            target: valueName,
            value: value
        },
        dataType: 'json',
        success: function (output, textStatus, jqXHR) {
            if (output.success == 'true') {
                failText.hide();
                successText.show();
            } else {
                successText.hide();
                failText.show();
            }
        },
        error: function (jqXHR, textStatus, errorThrown) {
            successText.hide();
            failText.show();
        },
        complete: function (jqXHR, status) {
            updateButton.disabled = false;
            running.splice(running.indexOf(programMame), 1)
        }
    });
}