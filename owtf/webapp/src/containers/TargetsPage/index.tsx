/*
 * Targets Page
 * Handles adding & deleting targest
 * Handles running plugins on different targets
 * Shows the list of targets along with actions to apply on the targets
 */

import React, {useState, useEffect} from "react";
import {
  Pane,
  Heading,
  Button,
  Textarea,
  Icon,
  Alert,
  Spinner,
  ImportIcon,
  BuildIcon
} from "evergreen-ui";
import Sessions from "../Sessions/index";
import Plugins from "../Plugins/index";
import TargetsTable from "./TargetsTable";
// import "./style.scss";
import PropTypes from "prop-types";
import { connect, useSelector, useDispatch  } from "react-redux";
import { createStructuredSelector } from "reselect";
import {
  makeSelectFetchError,
  makeSelectFetchLoading,
  makeSelectFetchTargets,
  makeSelectCreateLoading,
  makeSelectCreateError
} from "./selectors";
import { makeSelectFetchSessions } from "../Sessions/selectors";
import { loadTargets, createTarget } from "./actions";
import { loadSessions } from "../Sessions/actions";
import TargetList from "../Transactions/TargetList";

const IMPORT_STR = "import";
const BUILD_STR = "build";

interface ITargetsProps {
  fetchLoading: boolean;
  fetchError: object | boolean;
  targets: Array<any> | boolean;
  sessions: Array<any> | boolean;
  onFetchTarget: Function;
  createLoading: boolean;
  createError: object | boolean;
  onCreateTarget: Function;
  onFetchSession: Function;
};

export function TargetsPage({
  fetchLoading,
  fetchError,
  targets,
  sessions,
  onFetchTarget,
  createLoading,
  createError,
  onCreateTarget,
  onFetchSession
}: ITargetsProps) {
  
  const [newTargetUrls, setNewTargetUrls] = useState(""); //URLs of new targets to be added
  const [show, setShow] = useState(false); //handles visibility of alert box
  const [alertStyle, setAlertStyle] = useState("");
  const [alertMsg, setAlertMsg] = useState("");
  const [disabled, setDisabled] = useState(false); //for target URL textbox
  const [pluginShow, setPluginShow] = useState(false); //handles plugin component
  const [selectedTargets, setSelectedTargets] = useState([]);

  /**
   * Function re-initializing the state after plugin launch
   */
  const resetTargetState = () => {
    setSelectedTargets([])
  }

  /**
   * Function handles the closing of Alert box
   */
  const handleDismiss = () => {
    setShow(false);
  };

  /**
   * Function rendering the Alert box after plugins launch or targets adding
   */
  const renderAlert = () => {
    let msgHeader = "";
    switch (alertStyle) {
      case "danger":
        msgHeader = "Oops!";
        break;
      case "success":
        msgHeader = "Yup!";
        break;
      case "warning":
        msgHeader = "Hey!";
        break;
      case "none":
        msgHeader = "BTW!";
        break;
      default:
        msgHeader = "";
    }
    if (show) {
      return (
        <Alert
          appearance="card"
          intent={alertStyle}
          title={msgHeader}
          isRemoveable={true}
          onRemove={handleDismiss}
        >
          {alertMsg}
        </Alert>
      );
    }
  }

  /**
   * Function invoking the Alert box using given params
   * @param {string} alertStyle Intent of the alert box
   * @param {string} alertMsg Message shown by the alert box
   */
  const handleAlertMsg = (alertStyle: string, alertMsg: string) => {
    setShow(true);
    setAlertStyle(alertStyle);
    setAlertMsg(alertMsg);
    setTimeout(() => {
      setShow(false);
    }, 5000);
  }

  /**
   * Function updating the input targets url
   * @param {Object} event Event containing the name and value of the Textbox
   */
  const handleTargetUrlsChange = ({ target }: any) => {
    setSelectedTargets(
      target.value
    );
  }

  /**
   * Function validating a string to be a proper URL
   * @param {string} str String to be validated
   */
  const isUrl = (str: string) => {
    // TODO: Add all url protocols to support network plugins
    const urlPattern = /(http|ftp|https):\/\/[\w-]+(\.[\w-]+)+([\w.,@?^=%&amp;:\/~+#-]*[\w@?^=%&amp;\/~+#-])?/;
    return urlPattern.test(str);
  }

  /**
   * Function for adding new targets using the onCreateTarget function
   */
  const addNewTargets = () => {
    setDisabled(true);
    const lines = newTargetUrls.split("\n");
    const targetUrls: Array<any> = [];
    lines.map(line => {
      if (isUrl(line)) {
        // Check if a valid url
        targetUrls.push(line);
        setNewTargetUrls("");
      } else if (isUrl("http://" + line)) {
        // If not valid url and adding http:// makes it a valid url
        targetUrls.push("http://" + line);
        targetUrls.push("https://" + line);
        setNewTargetUrls("");
      } else {
        handleAlertMsg("danger", line + " is not a valid url");
      }
    });

    // Since we only have valid urls now in targetUrls, add them using api
    // Proceed only if there is atleast one valid url
    if (targetUrls.length > 0) {
      targetUrls.map(target_url => {
        onCreateTarget(target_url);
        setTimeout(() => {
          if (createError !== false) {
            handleAlertMsg(
              "danger",
              "Unable to add " + unescape(target_url.split("//")[1])
            );
          }
        }, 200);
      });
      handleAlertMsg(
        "none",
        "Targets are being added in the background, and will appear in the table soon"
      );
    }
    setDisabled(false);
  }

  useEffect(() => {
    onFetchTarget();
    onFetchSession();
  }, []);

  /**
   * Function returns the current session
   */
  const getCurrentSession = () => {
    if (sessions === false) return false;
    if(sessions !== true){
      for (const session of sessions) {
        if (session.active) return session;
      }
    }
  }

  /**
   * Function to download list of targets as txt file
   */
  const exportTargets = () => {
    const targetsArray: Array<any> = [];
    if(targets instanceof Array){
      targets.map(target=> {
        targetsArray.push(target.target_url + "\n");
      });
    }
    const element = document.createElement("a");
    const file = new Blob(targetsArray, { type: "text/plain;charset=utf-8" });
    element.href = URL.createObjectURL(file);
    element.download = "targets.txt";
    element.click();
  }

  /**
   * Handles the closing of the plugin component
   */
  const handlePluginClose = () => {
    setPluginShow(false);
  }

  /**
   * Handles the opening of the plugin component
   */
  const handlePluginShow = () => {
    setPluginShow(false);
  }

  /**
   * Function updating the targest IDs to be run
   * @param {Array} selectedTargets List of IDs of the targets to be run
   */
  const updateSelectedTargets = (selectedTargets: any) => {
    setSelectedTargets(selectedTargets);
  }


  const TargetsTableProps = {
    targets: targets,
    handleAlertMsg: handleAlertMsg,
    getCurrentSession: getCurrentSession,
    updateSelectedTargets: updateSelectedTargets,
    handlePluginShow: handlePluginShow
  };
  const PluginProps = {
    handlePluginClose: handlePluginClose,
    pluginShow: pluginShow,
    selectedTargets: selectedTargets,
    handleAlertMsg: handleAlertMsg,
    resetTargetState: resetTargetState
  };
  return (
    <Pane margin={20} data-test="targetsPageComponent">
      {renderAlert()}
      <Pane
        clearfix
        display="flex"
        flexDirection="row"
        flexWrap="wrap"
        justifyContent="center"
        overflow="hidden"
      >
        <Pane id="add_targets" width="40%" margin={20}>
          <Pane flexDirection="column">
            <Heading size={700} color="#0788DE">
              Add Targets
            </Heading>
            <Textarea
              name="newTargetUrls"
              placeholder="Input targets seperated by new line"
              marginTop={10}
              onChange={handleTargetUrlsChange}
              value={newTargetUrls}
            />
            <Button
              appearance="primary"
              marginTop={10}
              disabled={disabled}
              onClick={addNewTargets}
              data-test="addTargetButton"
            >
              Add Targets
            </Button>
            <Plugins {...PluginProps} />
          </Pane>
        </Pane>
        <Pane margin={40} flex={1}>
          <Pane display="flex" padding={16}>
            <Pane flex={1} alignItems="center" display="flex">
              <Heading size={700}>TARGETS</Heading>
            </Pane>
            <Pane marginRight={16}>
              <Sessions />
            </Pane>
            <Pane>
              <Button onClick={exportTargets}>
                <ImportIcon marginRight={10} />
                Export
              </Button>
              <Button
                appearance="primary"
                intent="success"
                onClick={handlePluginShow}
                data-test="pluginButton"
              >
                <BuildIcon marginRight={10} />
                Run
              </Button>
            </Pane>
          </Pane>
          {fetchError !== false ? (
            <p>Something went wrong, please try again!</p>
          ) : null}
          {fetchLoading !== false ? (
            <Pane
              display="flex"
              alignItems="center"
              justifyContent="center"
              height={400}
            >
              <Spinner size={64} />
            </Pane>
          ) : null}
          {targets !== false ? <TargetsTable {...TargetsTableProps} /> : null}
        </Pane>
      </Pane>
    </Pane>
  );
  
}

TargetsPage.propTypes = {
  fetchLoading: PropTypes.bool,
  fetchError: PropTypes.oneOfType([PropTypes.object, PropTypes.bool]),
  targets: PropTypes.oneOfType([PropTypes.array, PropTypes.bool]),
  sessions: PropTypes.oneOfType([PropTypes.array, PropTypes.bool]),
  onFetchTarget: PropTypes.func,
  createLoading: PropTypes.bool,
  createError: PropTypes.oneOfType([PropTypes.object, PropTypes.bool]),
  onCreateTarget: PropTypes.func
};

const mapStateToProps = createStructuredSelector({
  sessions: makeSelectFetchSessions,
  targets: makeSelectFetchTargets,
  fetchLoading: makeSelectFetchLoading,
  fetchError: makeSelectFetchError,
  createLoading: makeSelectCreateLoading,
  createError: makeSelectCreateError
});

const mapDispatchToProps = (dispatch: Function) => {
  return {
    onFetchSession: () => dispatch(loadSessions()),
    onFetchTarget: () => dispatch(loadTargets()),
    onCreateTarget: (target_url: string) => dispatch(createTarget(target_url))
  };
};

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(TargetsPage);
