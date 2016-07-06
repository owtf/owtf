import React from 'react';
import {muiTheme, TRANSACTION_API_URL} from './constants';
import FlatButton from 'material-ui/FlatButton';
import RaisedButton from 'material-ui/RaisedButton';
import Dialog from 'material-ui/Dialog';
import TextField from 'material-ui/TextField';
const style = {
    margin: 12
};


export class Footer extends React.Component {

    constructor(props) {
        super(props);

        this.state = {
            open: false,
            modalMessages: ""
        };

        this.handleClose = this.handleClose.bind(this);
        this.handleOpen = this.handleOpen.bind(this);
        this.requestSender = this.requestSender.bind(this);
        this.checkIfFileExists = this.checkIfFileExists.bind(this);
    };

    handleOpen() {
        this.setState({open: true, modalMessages: ""});
    };

    handleClose() {
        this.setState({open: false, modalMessages: ""});
    };

    verifyFileName(elem) {
        var alphaExp = /^[0-9a-zA-Z]+$/;
        if(elem.match(alphaExp)){
          return true;
        } else {
          this.setState({modalMessages: "Incorrect File Name(only alphanumeric characters allowed)"});
        }
    };

    checkIfFileExists(data, Status, xhr) {
      this.handleClose.call();
      this.context.closeZestState.call();
      if(data.exists!="true"){
          this.context.alert("Script Created :D");
      }
      else {
          this.context.alert("Script with this name already exists !");
      }
    };


    requestSender() {
      var file_name = this.refs.zestscriptname.getValue();
      var checkIfFileExists = this.checkIfFileExists.bind(this);
      var validateFilename = this.verifyFileName.bind(this, file_name);
      if(validateFilename.call()){
          var errorAlert = this.context.alert;
          var trans = this.context.selectedTransactionRows;
          var target_id = this.context.target_id;
          var trans_str=JSON.stringify(trans);
          $.ajax({
            url: TRANSACTION_API_URL.replace("target_id", target_id.toString()) + "zest",
            type:'POST',
            data:{trans:trans_str,name:file_name},
            success:checkIfFileExists,
            traditional: true,
            error:function(xhr, textStatus, serverResponse){
                errorAlert("Server replied: " + serverResponse);
            }
          });
        }
    };

    render() {
        const actions = [
          <FlatButton label="Cancel" primary={true} onTouchTap={this.handleClose}/>,
          <FlatButton label="Generate!" primary={true} keyboardFocused={true} onTouchTap={this.requestSender}/>,
        ];
        return (
            <div>
                <div className="navbar navbar-default navbar-fixed-bottom" id="#fixed_bar">
                    <div className="container">
                        <div style={{
                            textAlign: "center"
                        }}>
                            <RaisedButton backgroundColor="#009688" label="Send" labelColor="#fff" style={style} onTouchTap={this.handleOpen} disabled={this.context.selectedTransactionRows.length === 0}/>
                            <RaisedButton backgroundColor="#d9534f" label="Close" labelColor="#fff" style={style} onTouchTap={this.context.closeZestState}/>
                        </div>
                    </div>
                </div>
                <Dialog title="Enter Script Name :" actions={actions} modal={true} open={this.state.open}>
                  <TextField ref="zestscriptname" hintText="Type name here" errorText={this.state.modalMessages} floatingLabelText="Name of script" />
                </Dialog>
            </div>
        );
    }
}

Footer.contextTypes = {
    muiTheme: React.PropTypes.object.isRequired,
    selectedTransactionRows: React.PropTypes.array,
    target_id: React.PropTypes.number,
    closeZestState: React.PropTypes.func,
    alert: React.PropTypes.func,
};

export default Footer;
