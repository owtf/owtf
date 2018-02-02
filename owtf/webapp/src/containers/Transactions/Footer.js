import React from 'react';
import {TRANSACTION_API_URL} from './constants';

const style = {
    margin: 12
};

/**
  * React Component for Footer. It is child component used by Transactions.
  */

export class Footer extends React.Component {

    constructor(props) {
        super(props);

        this.state = {
            modalMessages: ""
        };

        this.handleClose = this.handleClose.bind(this);
        this.requestSender = this.requestSender.bind(this);
        this.checkIfFileExists = this.checkIfFileExists.bind(this);
    };

    handleClose() {
        $('#ScriptModal').modal('toggle');
    };

    /**
      * Function which tests that the provided script name for zest is correct or not (Regexically, only alphanumeric characters are allowed)
      */
    verifyFileName(elem) {
        var alphaExp = /^[0-9a-zA-Z]+$/;
        if (elem.match(alphaExp)) {
            return true;
        } else {
            this.setState({modalMessages: "Incorrect File Name(only alphanumeric characters allowed)"});
        }
    };

    /**
      * Function which tests that provided file name already exists or not.
      */

    checkIfFileExists(data, Status, xhr) {
        this.handleClose.call();
        this.context.closeZestState.call();
        if (data.exists != "true") {
            this.context.alert("Script Created :D");
        } else {
            this.context.alert("Script with this name already exists !");
        }
    };

    /**
      * Function which sends the reqeusts to server for zest script. It gives the file name and selected Transactions as a data in reqeust.
      * Uses REST API - /api/targets/target_id/transactions/
      */

    requestSender() {
        var file_name = this.refs.zestscriptname.value;
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
        return (
            <div>
                <div className="navbar navbar-default navbar-fixed-bottom" id="#fixed_bar">
                    <div className="container">
                        <div style={{
                            textAlign: "center"
                        }}>
                            <button style={style} type="button" className={this.context.selectedTransactionRows.length === 0
                                ? "btn btn-primary btn-lg disabled"
                                : "btn btn-primary btn-lg"} data-toggle="modal" data-target="#ScriptModal">Send</button>
                            <button style={style} type="button" className="btn btn-danger btn-lg" onTouchTap={this.context.closeZestState}>Close</button>
                        </div>
                    </div>
                </div>
                <div className="modal fade" id="ScriptModal" tabindex="-1" role="dialog" aria-labelledby="myModalLabel" aria-hidden="true">
                    <div className="modal-dialog-center">
                        <div className="modal-content">
                            <div className="modal-header">
                                <button type="button" className="close" data-dismiss="modal" aria-hidden="true">&times;</button>
                                <h4 className="modal-title" id="myModalLabel">Enter Script Name :</h4>
                                <h6 className="modal-title" id="name_tip">(only alphanumeric characters)</h6>
                            </div>
                            <div className="modal-body">
                                <p id="Filecheck">{this.state.modalMessages}</p>
                                <input type="text" ref="zestscriptname" id="textareaID" className="form-control"></input>
                            </div>
                            <div className="modal-footer">
                                <button type="button" className="btn btn-primary" id="saveBtn" onClick={this.requestSender.bind(this)}>Generate!</button>
                                <button type="button" className="btn btn-default" data-dismiss="modal">Cancel</button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        );
    }
}

Footer.contextTypes = {
    // selectedTransactionRows: React.PropTypes.array,
    // target_id: React.PropTypes.number,
    // closeZestState: React.PropTypes.func,
    // alert: React.PropTypes.func
};

export default Footer;