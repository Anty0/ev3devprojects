function extractConfig(programMame) {
    var idStart = programMame + '-';
    var result = {};
    $('input').filter(function (index, element) {
        return element.id.startsWith(idStart);
    }).each(function (index, element) {
        result[element.id.substring(idStart.length)] = element.value
    });
    return result;
}

function handleStartStopClick(programMame) {
    console.log('Called start/stop of ' + programMame);

    var stateText = $('#program-' + programMame + '-state');
    var startStopButton = $('#program-' + programMame + '-state-switch');
    var failText = $('program-' + programMame + '-fail-text');
    failText.hide();
    startStopButton.disabled = true;

    var config = extractConfig(programMame);

    $.ajax({
        async: true,
        method: 'POST',
        url: 'execute.esp',
        data: {
            name: programMame,
            config: JSON.stringify(config)
        },
        dataType: 'json',
        success: function(output, textStatus, jqXHR) {
            startStopButton[0].innerHTML = output.stateSwitchText;
            stateText[0].innerHTML = output.stateText;
        },
        error: function (jqXHR, textStatus, errorThrown) {
            failText.show();
        },
        complete: function (jqXHR, status) {
            startStopButton.disabled = false;
        }
    });
}

function handleUpdateConfigClick(programMame) {
    console.log('Called update config of ' + programMame);
}

function handleConfigChange(programMame, configName) {
    console.log('Called config ' + configName + ' change of ' + programMame);
}