import React from 'react';
import {TRANSACTION_API_URL} from './constants';
import Dialog from 'react-toolbox/lib/dialog';
import Input from 'react-toolbox/lib/input';
import {Button} from 'react-toolbox/lib/button';
import CriticalButton from '../theme/buttons/Critical';
import LowButton from '../theme/buttons/Low';

const style = {
    margin: 12
};

export class Footer extends React.Component {

    constructor(props) {
        super(props);

        this.state = {
            scriptName: '',
            open: false,
            modalMessages: ""
        };

        this.handleClose = this.handleClose.bind(this);
        this.handleOpen = this.handleOpen.bind(this);
        this.requestSender = this.requestSender.bind(this);
        this.checkIfFileExists = this.checkIfFileExists.bind(this);
    };

    handleChange(value) {
        this.setState({scriptName: value});
    };

    handleOpen() {
        this.setState({open: true, modalMessages: ""});
    };

    handleClose() {
        this.setState({open: false, modalMessages: ""});
    };

    verifyFileName(elem) {
        var alphaExp = /^[0-9a-zA-Z]+$/;
        if (elem.match(alphaExp)) {
            return true;
        } else {
            this.setState({modalMessages: "Incorrect File Name(only alphanumeric characters allowed)"});
        }
    };

    checkIfFileExists(data, Status, xhr) {
        this.handleClose.call();
        this.context.closeZestState.call();
        if (data.exists != "true") {
            this.context.alert("Script Created :D");
        } else {
            this.context.alert("Script with this name already exists !");
        }
    };

    requestSender() {
        var file_name = this.state.scriptName;
        var checkIfFileExists = this.checkIfFileExists.bind(this);
        var validateFilename = this.verifyFileName.bind(this, file_name);
        if (validateFilename.call()) {
            var errorAlert = this.context.alert;
            var trans = this.context.selectedTransactionRows;
            var target_id = this.context.target_id;
            var trans_str = JSON.stringify(trans);
            $.ajax({
                url: TRANSACTION_API_URL.replace("target_id", target_id.toString()) + "zest",
                type: 'POST',
                data: {
                    trans: trans_str,
                    name: file_name
                },
                success: checkIfFileExists,
                traditional: true,
                error: function(xhr, textStatus, serverResponse) {
                    errorAlert("Server replied: " + serverResponse);
                }
            });
        }
    };

    render() {
        const actions = [
            {
                label: "Cancel",
                onClick: this.handleClose
            }, {
                label: "Generate!",
                onClick: this.requestSender
            }
        ];
        return (
            <div>
                <div className="navbar navbar-default navbar-fixed-bottom" id="#fixed_bar">
                    <div className="container">
                        <div style={{
                            textAlign: "center"
                        }}>
                            <LowButton label="Send" onTouchTap={this.handleOpen} disabled={this.context.selectedTransactionRows.length === 0} style={style} raised primary/>
                            <CriticalButton label="Close" onTouchTap={this.context.closeZestState} style={style} raised primary/>
                        </div>
                    </div>
                </div>
                <Dialog actions={actions} active={this.state.open} title='Enter Script Name :'>
                    <Input type='text' ref="zestscriptname" error={this.state.modalMessages} label='Type name here' value={this.state.scriptName} onChange={this.handleChange.bind(this)} hint="e.g helloWorld" required/>
                </Dialog>
            </div>
        );
    }
}

Footer.contextTypes = {
    selectedTransactionRows: React.PropTypes.array,
    target_id: React.PropTypes.number,
    closeZestState: React.PropTypes.func,
    alert: React.PropTypes.func
};

export default Footer;
