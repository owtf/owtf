import React from "react";
import { Circle } from "rc-progress";
import TimeAgo from "react-timeago";
import PropTypes from "prop-types";
import Dialog from "../../components/DialogBox/dialog";

/**
 *  React Component for one entry of Worker Panel legend.
 *  It is child components which is used by WorkerLegend
 *  Receives - {"busy": false, "name": "Worker-1", "work": [], "worker": 14733, "paused": false, "id": 1}, as an JS object from properties.
 *  work is array which contains the work assigned to that worker
 */

interface workerPanelPropsType {
  progressData: object,
  workerData: [],
  workerLogs: any,
  onFetchWorkerLogs: Function,
  pollInterval: number,
  data?: any
}
interface workerPanelStateType {
  showDialog: boolean,
  dialogContent: string,
  isDialogOpened: boolean
}


export class Worker extends React.Component<workerPanelPropsType, workerPanelStateType> {
  constructor(props) {
    super(props);
    this.getWork = this.getWork.bind(this);

    {/* @ts-ignore */}
    this.state = {
      showDialog: false,
      dialogContent: "Nothing to show here!",
      isDialogOpened: false
    };

    this.openDialog = this.openDialog.bind(this);
    this.closeDialog = this.closeDialog.bind(this);
  }

  // Function responsible for opening the dialog box
  openDialog() {
    this.setState({
      isDialogOpened: true
    });
  }

  // Function responsible for closing the dialog box
  closeDialog() {
    this.setState({
      isDialogOpened: false
    });
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
      this.setState({ isDialogOpened: true });
    };
    // This put the worker id with its currently running plugin in worker legend
    let Work;
    if (this.props.data.work.length > 0) {
      Work = (
        <div className="workerPanelComponentContainer__workerLegendContainer__workerComponentWrapper__workerComponent__workContainer">
          {/* Loading GIF if worker is busy */}
          <img
            className="workerpanel-labelimg"
            src={require("../../../public/img/Preloader.gif")}
          />
          <p>
            {"Worker " +
              this.props.data.id +
              " - " +
              this.props.data.work[1].name +
              " ("}
            <TimeAgo date={this.props.data.start_time} />
          </p>
          <button onClick={() => this.setState({ isDialogOpened: true })}>
            Log
          </button>
        </div>
      );
    } else {
      Work = (
        <div className="workerPanelComponentContainer__workerLegendContainer__workerComponentWrapper__workerComponent__workContainer">
          {/* Constant image if worker is not busy */}
          <img
            className="workerpanel-labelimg"
            src={require("../../../public/img/not-running.png")}
          />
          <p>{"Worker " + this.props.data.id + " - " + "Not Running "}</p>
          <button onClick={() => getLog(this.props.data.name)}>Log</button>
        </div>
      );
    }

    return Work;
  }

  render() {
    const { isDialogOpened } = this.state;

    return (
      <div
        className="workerPanelComponentContainer__workerLegendContainer__workerComponentWrapper__workerComponent"
        data-test="workerComponent"
      >
        {this.getWork()}

        <Dialog
          title="Worker-Log"
          isDialogOpened={isDialogOpened}
          onClose={this.closeDialog}
        >
          <div className="workerPanelComponentContainer__workerLegendContainer__workerComponentWrapper__workerComponent__workerLogContainer">
     
            <textarea rows={20} cols={50} value={this.state.dialogContent} disabled></textarea>
          </div>
        </Dialog>
      </div>
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


interface workerLegendPropsType {
  workerData: [],
  workerLogs: boolean | string,
  onFetchWorkerLogs: Function,
  pollInterval: number
}
interface WorkerLegendStateType {
  intervalId: any
}

export class WorkerLegend extends React.Component<workerLegendPropsType, WorkerLegendStateType> {
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
    this.props.workerData.map((worker: any) => {
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
    {/* @ts-ignore */}
    this.state.intervalId = setInterval(
      this.changeState,
      this.props.pollInterval
    );
  }

  render() {
    return (
      <div
        className="workerPanelComponentContainer__workerLegendContainer__workerComponentWrapper"
        data-test="workerLegendComponent"
      >
        {this.props.workerData.map((worker: any ,index) => {
          return (
            <div key={worker.id}>
              {/* @ts-ignore */}
              <Worker
                data={worker}
                workerLogs={this.props.workerLogs}
                onFetchWorkerLogs={this.props.onFetchWorkerLogs}
              />
            </div>

          );
        })}
      </div>
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


interface ProgressBarPropsType {
  pollInterval: number,
  progressData: any
}
interface ProgressBarStateType {
  percent: number,
  color: any,
  intervalId: any
}
export class ProgressBar extends React.Component<ProgressBarPropsType, ProgressBarStateType> {
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
    {/* @ts-ignore */}
    var randNumber = colorMap[parseInt(Math.random() * 3)]
    var left_count = this.props.progressData.left_count;
    var complete_count = this.props.progressData.complete_count;
    if (left_count == 0 && complete_count == 0) {
      this.setState({
        percent: 0,
        color: randNumber
      });
      clearInterval(this.state.intervalId);
    } else {

      var percentage_done = (complete_count / (left_count + complete_count)) * 100;
      {/* @ts-ignore */}
      var randColor1 = colorMap[parseInt(percentage_done / 34)];
      this.setState({
        percent: percentage_done,
        color: randColor1
      });
      if (percentage_done == 100) {
        clearInterval(this.state.intervalId);
      }
    }
  }

  componentDidMount() {
    this.changeState();
    {/* @ts-ignore */}
    this.state.intervalId = setInterval(
      this.changeState,
      this.props.pollInterval
    );
  }

  render() {
    return (
      <>
        {/* @ts-ignore */}
        <Circle height={280} percent={this.state.percent} strokeWidth="5" strokeColor={this.state.color} />
      </>

    );
  }
}

/**
 *  React Component for Worker Panel.
 *  It is child components which is used by Dashboard.js
 */

interface workerPanelPropsType {
  progressData: object,
  workerData: [],
  workerLogs: any,
  onFetchWorkerLogs: Function,
  pollInterval: number
}
interface workerPanelStateType {
  percent: number,
  color: any,
  intervalId: any
}

export default class WorkerPanel extends React.Component<workerPanelPropsType, workerPanelStateType>{
  render() {
    const {
      progressData,
      workerData,
      workerLogs,
      onFetchWorkerLogs,
      pollInterval
    } = this.props;
    return (
      <div
        className="workerPanelComponentContainer"
        data-test="workerPanelComponent"
      >
        <div className="workerPanelComponentContainer__progressbarContainer">
          <ProgressBar
            pollInterval={pollInterval}
            progressData={progressData}
          />
        </div>
        <div className="workerPanelComponentContainer__workerLegendContainer">
          {this.props.workerData ? (
            <WorkerLegend
              pollInterval={pollInterval}
              workerData={workerData}
              workerLogs={workerLogs}
              onFetchWorkerLogs={onFetchWorkerLogs}
            />
          ) : null}
        </div>
      </div>
    );
  }
}
