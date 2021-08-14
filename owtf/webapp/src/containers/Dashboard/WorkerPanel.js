import React from "react";
import { Pane, Dialog, Paragraph, Button } from "evergreen-ui";
import { Circle } from "rc-progress";
import TimeAgo from "react-timeago";
import PropTypes from "prop-types";

/**
 *  React Component for one entry of Worker Panel legend.
 *  It is child components which is used by WorkerLegend
 *  Receives - {"busy": false, "name": "Worker-1", "work": [], "worker": 14733, "paused": false, "id": 1}, as an JS object from properties.
 *  work is array which contains the work assigned to that worker
 */

export class Worker extends React.Component {
  constructor(props) {
    super(props);
    this.getWork = this.getWork.bind(this);

    this.state = {
      showDialog: false,
      dialogContent: "Nothing to show here!"
    };
  }

  /* Function resposible to make enteries for each worker in worker legend */
  getWork() {
    let getLog = name => {
      this.props.onFetchWorkerLogs(name, -1);
      setTimeout(() => {
        const workerLogs = this.props.workerLogs;
        if (workerLogs !== false) {
          this.setState({ dialogContent: workerLogs });
        }
      }, 500);
      this.setState({ showDialog: true });
    };
    // This put the worker id with its currently running plugin in worker legend
    let Work;
    if (this.props.data.work.length > 0) {
      Work = (
        <Pane
          display="flex"
          flexDirection="row"
          alignItems="center"
          justifyContent="center"
        >
          {/* Loading GIF if worker is busy */}
          <img
            className="workerpanel-labelimg"
            src={require("../../../public/img/Preloader.gif")}
          />
          <Paragraph>
            {"Worker " +
              this.props.data.id +
              " - " +
              this.props.data.work[1].name +
              " ("}
            <TimeAgo date={this.props.data.start_time} />)
          </Paragraph>
          <Button
            appearance="primary"
            height={20}
            onClick={() => this.setState({ showDialog: true })}
          >
            Log
          </Button>
        </Pane>
      );
    } else {
      Work = (
        <Pane
          display="flex"
          flexDirection="row"
          alignItems="center"
          justifyContent="center"
        >
          {/* Constant image if worker is not busy */}
          <img
            className="workerpanel-labelimg"
            src={require("../../../public/img/not-running.png")}
          />
          <Paragraph margin={10}>
            {"Worker " + this.props.data.id + " - " + "Not Running "}
          </Paragraph>
          <Button
            appearance="primary"
            height={20}
            onClick={() => getLog(this.props.data.name)}
          >
            Log
          </Button>
        </Pane>
      );
    }

    return Work;
  }

  render() {
    return (
      <Pane data-test="workerComponent">
        {this.getWork()}
        <Dialog
          isShown={this.state.showDialog}
          title="Worker-Log"
          onCloseComplete={() => this.setState({ showDialog: false })}
          hasFooter={false}
        >
          {this.state.dialogContent}
        </Dialog>
      </Pane>
    );
  }
}

/**
*  React Component for Worker legend.
*  It is child components which is used by WorkerPanel Component.
*  Uses Rest API -
      - /api/workers/ to get details of workers.
* JSON response object:
*  Array of JS objects containing the details of each worker.
*    [
*       {
*         "busy": false,
*         "name": "Worker-1",
*         "work": [],
*         "worker": 14733,
*         "paused": false,
*         "id": 1
*       }
*     ]
*  Each element of data array represent details of what each worker is doing.
*/

export class WorkerLegend extends React.Component {
  constructor(props) {
    super(props);

    this.state = {
      intervalId: null
    };

    this.changeState = this.changeState.bind(this);
  }

  /* Function responsible to show currently running plugin against corresponsing worker */
  changeState() {
    let count = 0;
    this.props.workerData.map(worker => {
      if (worker.busy) {
        count++;
      }
    });
    // If no worker is running then clear the interval Why? paste server resources
    if (count == 0) {
      clearInterval(this.state.intervalId);
    }
  }

  /* Making an AJAX request on source property */
  componentDidMount() {
    this.changeState();
    this.state.intervalId = setInterval(
      this.changeState,
      this.props.pollInterval
    );
  }

  render() {
    return (
      <Pane data-test="workerLegendComponent">
        {this.props.workerData.map(worker => {
          return (
            <Worker
              key={worker.id}
              data={worker}
              workerLogs={this.props.workerLogs}
              onFetchWorkerLogs={this.props.onFetchWorkerLogs}
            />
          );
        })}
      </Pane>
    );
  }
}

/**
 *  React Component for ProgressBar.
 *  It is child components which is used by WorkerPanel Component.
 *  Uses npm package - rc-progress (http://react-component.github.io/progress/) to create ProgressBar
 *  Uses Rest API -
        - /api/plugins/progress/ (Obtained from props) to get data for ProgressBar
        -
 * JSON response object:
 * - /api/plugins/progress/
 *     {
 *      "left_count": 0, // Represent how many are left to be to scanned
 *      "complete_count": // Represents how many plugins are scanned.
 *    }
 */

export class ProgressBar extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      percent: 0,
      color: "#3FC7FA",
      intervalId: null
    };

    this.changeState = this.changeState.bind(this);
  }

  /* Function responsible to make changes in state of progres Bar */
  changeState() {
    var colorMap = ["#FE8C6A", "#3FC7FA", "#85D262"];
    var left_count = this.props.progressData.left_count;
    var complete_count = this.props.progressData.complete_count;
    if (left_count == 0 && complete_count == 0) {
      this.setState({
        percent: 0,
        color: colorMap[parseInt(Math.random() * 3)]
      });
      clearInterval(this.state.intervalId);
    } else {
      var percentage_done =
        (complete_count / (left_count + complete_count)) * 100;
      this.setState({
        percent: percentage_done,
        color: colorMap[parseInt(percentage_done / 34)]
      });
      if (percentage_done == 100) {
        clearInterval(this.state.intervalId);
      }
    }
  }

  componentDidMount() {
    this.changeState();
    this.state.intervalId = setInterval(
      this.changeState,
      this.props.pollInterval
    );
  }

  render() {
    return (
      <Circle
        height={200}
        percent={this.state.percent}
        strokeWidth="6"
        strokeColor={this.state.color}
      />
    );
  }
}

/**
 *  React Component for Worker Panel.
 *  It is child components which is used by Dashboard.js
 */

export default class WorkerPanel extends React.Component {
  render() {
    const {
      progressData,
      workerData,
      workerLogs,
      onFetchWorkerLogs,
      pollInterval
    } = this.props;
    return (
      <Pane display="flex" flexDirection="row" data-test="workerPanelComponent">
        <Pane>
          <ProgressBar
            pollInterval={pollInterval}
            progressData={progressData}
          />
        </Pane>
        <Pane marginLeft={100} justifyContent="center">
          {this.props.workerData ? (
            <WorkerLegend
              pollInterval={pollInterval}
              workerData={workerData}
              workerLogs={workerLogs}
              onFetchWorkerLogs={onFetchWorkerLogs}
            />
          ) : null}
        </Pane>
      </Pane>
    );
  }
}

WorkerPanel.propTypes = {
  progressData: PropTypes.object,
  workerData: PropTypes.array,
  workerLogs: PropTypes.oneOfType([PropTypes.bool, PropTypes.string]),
  onFetchWorkerLogs: PropTypes.func,
  pollInterval: PropTypes.number
};

ProgressBar.propTypes = {
  pollInterval: PropTypes.number,
  progressData: PropTypes.object
};

WorkerLegend.propTypes = {
  workerData: PropTypes.array,
  workerLogs: PropTypes.oneOfType([PropTypes.bool, PropTypes.string]),
  onFetchWorkerLogs: PropTypes.func,
  pollInterval: PropTypes.number
};

Worker.propTypes = {
  data: PropTypes.object,
  workerLogs: PropTypes.oneOfType([PropTypes.bool, PropTypes.string]),
  onFetchWorkerLogs: PropTypes.func
};
