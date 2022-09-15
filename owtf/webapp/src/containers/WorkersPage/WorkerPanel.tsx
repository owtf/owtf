/* Worker Panel component
 *
 * Renders worker details individually inside a panel component
 *
 */
import React, {useState} from "react";
import {
  Pane,
  Heading,
  IconButton,
  Paragraph,
  Strong,
  Link,
  Menu,
  Button,
  Popover,
  Position,
  Pre
} from "evergreen-ui";
import Moment from "react-moment";
import PropTypes from "prop-types";

const panelStyle = {
  primary: "#337ab7",
  info: "#bce8f1",
  default: "#ddd"
};

interface IWorkerPanel{
  worker: object;
  resumeWorker: Function;
  pauseWorker: Function;
  abortWorker: Function;
  deleteWorker: Function;
  handleLogDialogShow: Function;
  handleLogDialogContent: Function;
  logDialogShow: boolean;
  workerLogs: string | boolean;
  onFetchWorkerLogs: Function;
  logDialogContent: string;
}

export default function WorkerPanel({
  worker,
  resumeWorker,
  pauseWorker,
  abortWorker,
  deleteWorker,
  handleLogDialogShow,
  handleLogDialogContent,
  logDialogShow,
  workerLogs,
  onFetchWorkerLogs,
  logDialogContent
}: IWorkerPanel) {
    
  const [showLogs, setShowLogs] = useState(false);

  /**
   * Function handles the state of Show log button [BUTTON/MENU]
   * Renders the show log menu
   */
  const displayLog = () => {
    setShowLogs(true);
    getWorkerLog(worker.name, -1);
  }

  /**
   * Function handles the state of Show log button [BUTTON/MENU]
   * Renders the show log button
   */
  const hideLog = () => {
    setShowLogs(false);
  }

  /**
   * Function handles the background state of worker panel
   */
  const getPanelStyle = () => {
    const workerr = worker;
    if (workerr.busy && !workerr.paused) {
      return panelStyle.primary;
    } else if (workerr.paused) {
      return panelStyle.info;
    } else {
      return panelStyle.default;
    }
  }

  /**
   * Function to get control buttons based on the present state of a worker
   * It return pause button if worker is active & vice versa
   */
  const getControlButtons = () => {
    const workerr = worker;
    if (workerr.busy) {
      if (workerr.paused) {
        return (
          <IconButton
            appearance="primary"
            icon="play"
            intent="success"
            height={24}
            onClick={() => resumeWorker(workerr.id)}
          />
        );
      } else {
        return (
          <Pane display="flex" flexDirection="row">
            <IconButton
              appearance="primary"
              icon="pause"
              intent="warning"
              height={24}
              onClick={() => pauseWorker(workerr.id)}
            />
            <IconButton
              appearance="primary"
              icon="cross"
              intent="danger"
              height={24}
              onClick={() => abortWorker(workerr.id)}
            />
          </Pane>
        );
      }
    } else {
      return (
        <IconButton
          appearance="primary"
          icon="cross"
          intent="danger"
          height={24}
          onClick={() => deleteWorker(workerr.id)}
        />
      );
    }
  }

  /**
   * Function handling log lines
   * @param {sring} name Worker name
   * @param {number} lines log lines to show
   */
  const getWorkerLog = (name, lines) => {
    onFetchWorkerLogs(name, lines);
    setTimeout(() => {
      const workerLogs = workerLogs;
      if(workerLogs!==false){
        handleLogDialogContent(workerLogs);
      }
    }, 500);
  }

  /**
   * Handles the rendering of worker log dialog box
   * @param {string} worker worker name
   * @param {number} lines Lines to render
   */
  const openLogModal = (worker, lines) => {
    getWorkerLog(worker, lines);
    handleLogDialogShow();
  }
  
  const style = getPanelStyle();
  return (
    <Pane
      elevation={1}
      width={500}
      float="left"
      display="flex"
      flexDirection="column"
      marginRight={40}
      marginBottom={20}
      elevation={3}
      data-test="workerPanelComponent"
    >
      <Heading height={40} background={style}>
        <Pane margin={10}>
          {"Worker " + worker.id}
          <Pane className="pull-right">{getControlButtons()}</Pane>
        </Pane>
      </Heading>
      <Pane padding={15}>
        <Paragraph>
          <Strong>PID: </Strong>
          {worker.worker}
        </Paragraph>
        {worker.start_time !== undefined ? (
          <Paragraph>
            <Strong>Start Time: </Strong>
            {worker.start_time + "(~"}{" "}
            <Moment date={worker.start_time} durationFromNow /> {")"}
          </Paragraph>
        ) : (
          <Paragraph>
            <Strong>Start Time: </Strong>N/A
          </Paragraph>
        )}
        {worker.work.length > 0 ? (
          <Pane>
            <Paragraph>
              <Strong>Target: </Strong>
              <Link href={"/targets/" + worker.work[0]["id"]}>
                {worker.work[0].target_url}
              </Link>
            </Paragraph>
            <Paragraph>
              <Strong>Plugin: </Strong>
              {worker.work[1].title}
            </Paragraph>
            <Paragraph>
              <Strong>Type: </Strong>
              {worker.work[1].type.replace("_", " ")}
            </Paragraph>
            <Paragraph>
              <Strong>Group: </Strong>
              {worker.work[1].group}
            </Paragraph>
          </Pane>
        ) : null}
        {!this.state.showLogs ? (
          <Button appearance="primary" height={20} onClick={displayLog}>
            Show logs
          </Button>
        ) : (
          <Pane>
            <Paragraph>
              <Strong>Logs: </Strong>
              <Popover
                position={Position.BOTTOM_LEFT}
                content={
                  <Menu>
                    <Menu.Group>
                      <Menu.Item onSelect={hideLog}>None</Menu.Item>
                      <Menu.Item
                        onSelect={() => openLogModal(worker.name, -1)}
                      >
                        All
                      </Menu.Item>
                      {[...Array(10)].map((_, i) => (
                        <Menu.Item
                          key={i + 1}
                          onSelect={() =>
                            openLogModal(worker.name, i.toString())
                          }
                        >
                          {i + 1}
                        </Menu.Item>
                      ))}
                    </Menu.Group>
                  </Menu>
                }
              >
                <Button
                  iconAfter="caret-down"
                  marginLeft={5}
                  height={20}
                  intent="danger"
                >
                  Lines
                </Button>
              </Popover>
            </Paragraph>
            <Pre marginTop={10}>{logDialogContent}</Pre>
          </Pane>
        )}
      </Pane>
    </Pane>
  );
}

WorkerPanel.propTypes = {
  worker: PropTypes.object,
  resumeWorker: PropTypes.func,
  pauseWorker: PropTypes.func,
  abortWorker: PropTypes.func,
  deleteWorker: PropTypes.func,
  handleLogDialogShow: PropTypes.func,
  handleLogDialogContent: PropTypes.func,
  logDialogShow: PropTypes.bool,
  workerLogs: PropTypes.oneOfType([PropTypes.string, PropTypes.bool]),
  onFetchWorkerLogs: PropTypes.func,
  logDialogContent: PropTypes.string,
};
