import React, {useState} from 'react';
import CopyToClipboard from 'react-copy-to-clipboard';
import { Notification } from 'react-notification';
import { Pane, Tablist, Tab, Paragraph, Pre, Button, Strong, TextInputField, SelectField } from 'evergreen-ui';
import './style.scss';
import PropTypes from 'prop-types';

interface ITransactionHeader{
  target_id: number,
  transactionHeaderData: object,
  hrtResponse: string,
  headerHeight: number,
  getHrtResponse: Function
}

export default function TransactionHeader ({
  target_id,
  transactionHeaderData,
  hrtResponse,
  headerHeight,
  getHrtResponse
}:ITransactionHeader) {

  const [hrtForm, setHrtForm] = useState(false);
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(1);
  const [language, setLanguage] = useState('');
  const [proxy, setProxy] = useState('');
  const [searchstring, setSearchString] = useState('');
  const [data, setData] = useState('');
  
  const handleSubmit = () => {
    const values = {
      'data': data,
      'language': language,
      'proxy': proxy,
      'searchstring': searchstring,
    };
    const transaction_id = transactionHeaderData.id;
    const target_id = target_id;
    getHrtResponse(target_id, transaction_id, values);
  }


  const displayHrtForm = () => {
    setHrtForm(!hrtForm);
  };

  const handleSnackBarRequestOpen = () => {
    setSnackbarOpen(true);
  };

  const handleSnackBarRequestClose = () => {
    setSnackbarOpen(false);
  };

  return (
    <Pane marginTop={20} data-test="transactionHeaderComponent">
      <Tablist marginBottom={16} flexBasis={240} marginRight={24}>
        <Tab
          key={1}
          id={1}
          onSelect={() => setSelectedIndex(1)}
          isSelected={selectedIndex === 1}
          aria-controls={`panel-request`}
        >
          Request
        </Tab>
        <Tab
          key={2}
          id={2}
          onSelect={() => setSelectedIndex(2)}
          isSelected={selectedIndex === 2}
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
          aria-hidden={selectedIndex !== 1}
          display={selectedIndex === 1 ? 'block' : 'none'}
          height={headerHeight}
        >
          <Paragraph>Request Header</Paragraph>
          <Pre marginBottom={20}>{transactionHeaderData.requestHeader}</Pre>
          {transactionHeaderData.requestHeader !== '' &&
            <Button
              appearance="primary"
              intent="success"
              className="pull-right"
              onClick={displayHrtForm}>
              Copy as
          </Button>
          }
          {transactionHeaderData.requestHeader !== '' && hrtForm &&
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
                  value={proxy}
                  onChange={(e: { target: { value: React.SetStateAction<string>; }; }) => setProxy(e.target.value)}
                  marginRight={20}
                />
                <TextInputField
                  name="searchString"
                  label="Search String:"
                  placeholder="Search String"
                  value={searchstring}
                  onChange={(e: { target: { value: React.SetStateAction<string>; }; }) => setSearchString(e.target.value)}
                  marginRight={20}
                />
                <TextInputField
                  name="data"
                  label="Data:"
                  placeholder="data"
                  value={data}
                  onChange={(e: { target: { value: React.SetStateAction<string>; }; }) => setData(e.target.value)}
                  marginRight={20}
                />
              </Pane>
              <Pane className="pull-right" display="flex" flexDirection="row">
                <Button
                  appearance="primary"
                  intent="danger"
                  onClick={handleSubmit}>
                  Generate Code
                </Button>
                <CopyToClipboard text={hrtResponse}>
                  <Button
                    appearance="primary"
                    intent="success"
                    onClick={handleSnackBarRequestOpen}>
                    Copy to clipboard
                  </Button>
                </CopyToClipboard>
              </Pane>
              <Notification
                isActive={snackbarOpen}
                message="Copied to clipboard"
                action="close"
                dismissAfter={5000}
                onDismiss={handleSnackBarRequestClose}
                onClick={handleSnackBarRequestClose}
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
          aria-hidden={selectedIndex !== 2}
          display={selectedIndex === 2 ? 'block' : 'none'}
          height={headerHeight}
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

TransactionHeader.propTypes = {
  target_id: PropTypes.number,
  transactionHeaderData: PropTypes.object,
  hrtResponse: PropTypes.string,
  headerHeight: PropTypes.number,
  getHrtResponse: PropTypes.func
};
