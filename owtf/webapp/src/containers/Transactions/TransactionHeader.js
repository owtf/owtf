import React from 'react';
import CopyToClipboard from 'react-copy-to-clipboard';
import { Notification } from 'react-notification';
import { Pane, Tablist, Tab, Paragraph, Pre, Button, Strong, TextInputField, SelectField } from 'evergreen-ui';
import './style.scss';
import PropTypes from 'prop-types';

export default class TransactionHeader extends React.Component {

  constructor(props) {
    super(props);

    this.state = {
      hrtForm: false,
      snackbarOpen: false,
      selectedIndex: 1,
      language: '',
      proxy: '',
      searchstring: '',
      data: '',
    };

    this.handleSubmit = this.handleSubmit.bind(this);
    this.displayHrtForm = this.displayHrtForm.bind(this);
    this.handleSnackBarRequestClose = this.handleSnackBarRequestClose.bind(this);
    this.handleSnackBarRequestOpen = this.handleSnackBarRequestOpen.bind(this);
  };

  handleSubmit(event) {
    event.preventDefault();
    const values = {
      'data': this.state.data,
      'language': this.state.language,
      'proxy': this.state.proxy,
      'searchstring': this.state.searchstring,
    };
    const transaction_id = this.props.transactionHeaderData.id;
    const target_id = this.props.target_id;
    this.props.getHrtResponse(target_id, transaction_id, values);
  }


  displayHrtForm() {
    this.setState({ hrtForm: !this.state.hrtForm });
  };

  handleSnackBarRequestOpen() {
    this.setState({ snackbarOpen: true });
  };

  handleSnackBarRequestClose() {
    this.setState({ snackbarOpen: false });
  };

  render() {
    const { target_id, transactionHeaderData, hrtResponse, getHrtResponse, height } = this.props;
    return (
      <Pane marginTop={20}>
        <Tablist marginBottom={16} flexBasis={240} marginRight={24}>
          <Tab
            key={1}
            id={1}
            onSelect={() => this.setState({ selectedIndex: 1 })}
            isSelected={this.state.selectedIndex === 1}
            aria-controls={`panel-request`}
          >
            Request
          </Tab>
          <Tab
            key={2}
            id={2}
            onSelect={() => this.setState({ selectedIndex: 2 })}
            isSelected={this.state.selectedIndex === 2}
            aria-controls={`panel-response`}
          >
            Response
          </Tab>
        </Tablist>
        <Pane padding={16} background="tint1" flex="1">
          <Pane
            key={1}
            id={`panel-request`}
            role="tabpanel"
            aria-labelledby='request'
            aria-hidden={this.state.selectedIndex !== 1}
            display={this.state.selectedIndex === 1 ? 'block' : 'none'}
            height={height}
          >
            <Paragraph>Request Header</Paragraph>
            <Pre marginBottom={20}>{transactionHeaderData.requestHeader}</Pre>
            {transactionHeaderData.requestHeader !== '' &&
              <Button
                appearance="primary"
                intent="success"
                className="pull-right"
                onClick={this.displayHrtForm}>
                Copy as
            </Button>
            }
            {transactionHeaderData.requestHeader !== '' && this.state.hrtForm &&
              <Pane marginTop={50}>
                <Strong>Generate Code</Strong>
                <Pane display="flex" flexDirection="row">
                  <SelectField width={150} label="Language:" name="language" marginRight={20}>
                    <option value="bash">Bash</option>
                    <option value="python">Python</option>
                    <option value="php">PHP</option>
                    <option value="ruby">Ruby</option>
                  </SelectField>
                  <TextInputField
                    name="proxy"
                    label="Proxy:"
                    placeholder="proxy:port"
                    value={this.state.proxy}
                    onChange={e => this.setState({ proxy: e.target.value })}
                    marginRight={20}
                  />
                  <TextInputField
                    name="searchString"
                    label="Search String:"
                    placeholder="Search String"
                    value={this.state.searchstring}
                    onChange={e => this.setState({ searchstring: e.target.value })}
                    marginRight={20}
                  />
                  <TextInputField
                    name="data"
                    label="Data:"
                    placeholder="data"
                    value={this.state.data}
                    onChange={e => this.setState({ data: e.target.value })}
                    marginRight={20}
                  />
                </Pane>
                <Pane className="pull-right" display="flex" flexDirection="row">
                  <Button
                    appearance="primary"
                    intent="danger"
                    onClick={this.handleSubmit}>
                    Generate Code
                  </Button>
                  <CopyToClipboard text={hrtResponse}>
                    <Button
                      appearance="primary"
                      intent="success"
                      onClick={this.handleSnackBarRequestOpen}>
                      Copy to clipboard
                    </Button>
                  </CopyToClipboard>
                </Pane>
                <Notification
                  isActive={this.state.snackbarOpen}
                  message="Copied to clipboard"
                  action="close"
                  dismissAfter={5000}
                  onDismiss={this.handleSnackBarRequestClose}
                  onClick={this.handleSnackBarRequestClose}
                />
                <Pre marginTop={40}>{hrtResponse}</Pre>
              </Pane>
            }
          </Pane>
          <Pane
            key={2}
            id={`panel-response`}
            role="tabpanel"
            aria-labelledby='response'
            aria-hidden={this.state.selectedIndex !== 2}
            display={this.state.selectedIndex === 2 ? 'block' : 'none'}
            height={height}
          >
            <Paragraph>Response Header</Paragraph>
            <Pre marginBottom={20}>{transactionHeaderData.requestHeader}</Pre>
            <Paragraph>Response Body</Paragraph>
            <Pre marginBottom={20}>{transactionHeaderData.responseBody}</Pre>
          </Pane>
        </Pane>
      </Pane>
    );
  }
}

TransactionHeader.propTypes = {
  target_id: PropTypes.number,
  transactionHeaderData: PropTypes.object,
  hrtResponse: PropTypes.string,
  headerHeight: PropTypes.number,
  getHrtResponse: PropTypes.func
};
