import React from "react";
import CopyToClipboard from "react-copy-to-clipboard";
import { Notification } from "react-notification";
import { Pre } from "evergreen-ui";
import "./style.scss";

interface propsType {
  target_id: number;
  transactionHeaderData: any;
  hrtResponse: string;
  headerHeight: number;
  getHrtResponse: Function;
}
interface stateType {
  hrtForm: boolean;
  snackbarOpen: boolean;
  selectedIndex: number;
  language: any;
  proxy: any;
  searchstring: any;
  data: any;
}

export default class TransactionHeader extends React.Component<
  propsType,
  stateType
> {
  constructor(props) {
    super(props);

    this.state = {
      hrtForm: false,
      snackbarOpen: false,
      selectedIndex: 1,
      language: "",
      proxy: "",
      searchstring: "",
      data: ""
    };

    this.handleSubmit = this.handleSubmit.bind(this);
    this.displayHrtForm = this.displayHrtForm.bind(this);
    this.handleSnackBarRequestClose = this.handleSnackBarRequestClose.bind(
      this
    );
    this.handleSnackBarRequestOpen = this.handleSnackBarRequestOpen.bind(this);
  }

  handleSubmit() {
    const values = {
      data: this.state.data,
      language: this.state.language,
      proxy: this.state.proxy,
      searchstring: this.state.searchstring
    };

    const transaction_id = this.props.transactionHeaderData.id;
    const target_id = this.props.target_id;
    this.props.getHrtResponse(target_id, transaction_id, values);
  }

  displayHrtForm() {
    this.setState({ hrtForm: !this.state.hrtForm });
  }

  handleSnackBarRequestOpen() {
    this.setState({ snackbarOpen: true });
  }

  handleSnackBarRequestClose() {
    this.setState({ snackbarOpen: false });
  }

  render() {
    const { transactionHeaderData, hrtResponse } = this.props;

    return (
      <div
        className="transactionsHeader"
        data-test="transactionHeaderComponent"
      >
        <div className="transactionsHeader__requestResponseHeaderToggle">
          <span
            key={1}
            id="1"
            onClick={() => this.setState({ selectedIndex: 1 })}
            style={{
              backgroundColor:
                this.state.selectedIndex === 1
                  ? "rgba(0, 0, 0, 0.178)"
                  : "transparent"
            }}
          >
            Request
          </span>
          <span
            key={2}
            id="2"
            onClick={() => this.setState({ selectedIndex: 2 })}
            style={{
              backgroundColor:
                this.state.selectedIndex === 2
                  ? "rgba(0, 0, 0, 0.178)"
                  : "transparent"
            }}
          >
            Response
          </span>
        </div>

        <div className="transactionsHeader__requestResponseHeaderContainer__request">
          <div
            key={1}
            id={`panel-request`}
            role="tabpanel"
            aria-labelledby="request"
            aria-hidden={this.state.selectedIndex !== 1}
            style={{
              display: this.state.selectedIndex === 1 ? "block" : "none"
            }}
            className="transactionsHeader__requestResponseHeaderContainer__request__wrapper"
          >
            <p>Request Header</p>
            <pre>{transactionHeaderData.requestHeader}</pre>
            {transactionHeaderData.requestHeader !== "" && (
              <button className="pull-right" onClick={this.displayHrtForm}>
                Copy as
              </button>
            )}
            {transactionHeaderData.requestHeader !== "" && this.state.hrtForm && (
              <div className="transactionsHeader__requestResponseHeaderContainer__request__wrapper__generateCodeContainer">
                <strong>Generate Code</strong>
                <div className="transactionsHeader__requestResponseHeaderContainer__request__wrapper__generateCodeContainer__filterContainer">
                  <div className="transactionsHeader__requestResponseHeaderContainer__request__wrapper__generateCodeContainer__filterContainer__language">
                    <span>Language :</span>
                    <select
                      onChange={e => {
                        this.setState({
                          language: e.target.value
                        });
                      }}
                    >
                      <option value="bash">Bash</option>
                      <option value="python">Python</option>
                      <option value="php">PHP</option>
                      <option value="ruby">Ruby</option>
                    </select>
                  </div>

                  <div className="transactionsHeader__requestResponseHeaderContainer__request__wrapper__generateCodeContainer__filterContainer__proxy">
                    <span>Proxy:</span>
                    <input
                      type="text"
                      name="proxy"
                      placeholder="proxy:port"
                      value={this.state.proxy}
                      onChange={e => this.setState({ proxy: e.target.value })}
                    />
                  </div>

                  <div className="transactionsHeader__requestResponseHeaderContainer__request__wrapper__generateCodeContainer__filterContainer__searchString">
                    <span>Search String:</span>
                    <input
                      type="text"
                      name="searchString"
                      placeholder="Search String"
                      value={this.state.searchstring}
                      onChange={e =>
                        this.setState({ searchstring: e.target.value })
                      }
                    />
                  </div>

                  <div className="transactionsHeader__requestResponseHeaderContainer__request__wrapper__generateCodeContainer__filterContainer__data">
                    <span>Data:</span>
                    <input
                      type="text"
                      name="data"
                      placeholder="data"
                      value={this.state.data}
                      onChange={e => this.setState({ data: e.target.value })}
                    />
                  </div>
                </div>

                <div className="transactionsHeader__requestResponseHeaderContainer__request__wrapper__generateCodeContainer__buttonsContainer">
                  <button
                    onClick={() => {
                      this.handleSubmit;
                    }}
                  >
                    Generate Code
                  </button>
                  <CopyToClipboard text={hrtResponse}>
                    <button
                      onClick={() => {
                        this.handleSnackBarRequestOpen;
                      }}
                    >
                      Copy to clipboard
                    </button>
                  </CopyToClipboard>
                </div>
                <Notification
                  isActive={this.state.snackbarOpen}
                  message="Copied to clipboard"
                  action="close"
                  dismissAfter={5000}
                  onDismiss={this.handleSnackBarRequestClose}
                  onClick={this.handleSnackBarRequestClose}
                />
                <Pre marginTop={40}>{hrtResponse}</Pre>
              </div>
            )}
          </div>

          <div
            className="transactionsHeader__requestResponseHeaderContainer__response"
            key={2}
            id={`panel-response`}
            role="tabpanel"
            aria-labelledby="response"
            style={{
              display: this.state.selectedIndex === 2 ? "block" : "none"
            }}
          >
            <p>Response Header</p>
            <pre>{transactionHeaderData.requestHeader}</pre>
            <p>Response Body</p>
            <pre>{transactionHeaderData.responseBody}</pre>
          </div>
        </div>
      </div>
    );
  }
}
