/* Worker Panel component
 *
 * Renders worker details individually inside a panel component
 *
 */
import React from "react";
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
export default class WorkerPanel extends React.Component {
  constructor(props) {
    super(props);

    this.getPanelStyle = this.getPanelStyle.bind(this);
    this.getControlButtons = this.getControlButtons.bind(this);
    this.getWorkerLog = this.getWorkerLog.bind(this);
    this.displayLog = this.displayLog.bind(this);
    this.hideLog = this.hideLog.bind(this);
    this.openLogModal = this.openLogModal.bind(this);

    this.state = {
      showLogs: false
    };
  }

  /**
   * Function handles the state of Show log button [BUTTON/MENU]
   * Renders the show log menu
   */
  displayLog() {
    this.setState({ showLogs: true });
    this.getWorkerLog(this.props.worker.name, -1);
  }

  /**
   * Function handles the state of Show log button [BUTTON/MENU]
   * Renders the show log button
   */
  hideLog() {
    this.setState({ showLogs: false });
  }

  /**
   * Function handles the background state of worker panel
   */
  getPanelStyle() {
    const worker = this.props.worker;
    if (worker.busy && !worker.paused) {
      return panelStyle.primary;
    } else if (worker.paused) {
      return panelStyle.info;
    } else {
      return panelStyle.default;
    }
  }

  /**
   * Function to get control buttons based on the present state of a worker
   * It return pause button if worker is active & vice versa
   */
  getControlButtons() {
    const worker = this.props.worker;
    if (worker.busy) {
      if (worker.paused) {
        return (
          <IconButton
            appearance="primary"
            icon="play"
            intent="success"
            height={24}
            onClick={() => this.props.resumeWorker(worker.id)}
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
              onClick={() => this.props.pauseWorker(worker.id)}
            />
            <IconButton
              appearance="primary"
              icon="cross"
              intent="danger"
              height={24}
              onClick={() => this.props.abortWorker(worker.id)}
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
          onClick={() => this.props.deleteWorker(worker.id)}
        />
      );
    }
  }

  /**
   * Function handling log lines
   * @param {sring} name Worker name
   * @param {number} lines log lines to show
   */
  getWorkerLog(name, lines){
    this.props.onFetchWorkerLogs(name, lines);
    setTimeout(() => {
      const workerLogs = this.props.workerLogs;
      if(workerLogs!==false){
        this.props.handleLogDialogContent(workerLogs);
      }
    }, 500);
  }

  /**
   * Handles the rendering of worker log dialog box
   * @param {string} worker worker name
   * @param {number} lines Lines to render
   */
  openLogModal(worker, lines) {
    this.getWorkerLog(worker, lines);
    this.props.handleLogDialogShow();
  }

  render() {
    const { worker, logDialogContent } = this.props;
    const style = this.getPanelStyle();
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
            <Pane className="pull-right">{this.getControlButtons()}</Pane>
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
            <Button appearance="primary" height={20} onClick={this.displayLog}>
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
                        <Menu.Item onSelect={this.hideLog}>None</Menu.Item>
                        <Menu.Item
                          onSelect={() => this.openLogModal(worker.name, -1)}
                        >
                          All
                        </Menu.Item>
                        {[...Array(10)].map((_, i) => (
                          <Menu.Item
                            key={i + 1}
                            onSelect={() =>
                              this.openLogModal(worker.name, i.toString())
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
