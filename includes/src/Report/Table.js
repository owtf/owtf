import React from 'react';

class Table extends React.Component {

    render() {
        var obj = this.props.obj;
        var output_path = obj['output_path'];
        var status = obj['status'];
        var run_time = obj['run_time'];
        var start_time = obj['start_time'];
        var end_time = obj['end_time'];
        var run_time = obj['status'];
        var output = obj['output'];
        return (
            <table className="table table-bordered table-striped table-hover">
                <thead>
                    <tr>
                        <th>
                            RUNTIME
                        </th>
                        <th>
                            TIME INTERVAL
                        </th>
                        <th>
                            STATUS
                        </th>
                        {(() => {
                            if (output_path !== undefined) {
                                return (
                                    <th>
                                        OUTPUT FILES
                                    </th>
                                );
                            }
                        })()}
                        <th>
                            ACTIONS
                        </th>
                    </tr>
                </thead>
                <tbody>
                    <tr className={(() => {
                        switch (status) {
                            case "Aborted":
                                return "alert alert-warning";
                            case "Successful":
                                return "alert alert-success";
                            case "Crashed":
                                return "alert alert-error";
                            case "Running":
                                return "alert alert-info";
                            case "Skipped":
                                return "muted";
                            default:
                                return "";
                        }
                    })()}>
                        <td>
                            {run_time}
                        </td>
                        <td>
                            {start_time}
                            <br/>{end_time}
                        </td>
                        <td>
                            {status}
                        </td>
                        {(() => {
                            if (output_path !== undefined) {
                                return (
                                    <td>
                                        <a href="" target="_blank" className="btn btn-primary">Browse</a>
                                    </td>
                                );
                            }
                        })()}
                        <td>
                            <div className="btn-group">
                                <button className="btn btn-success" data-toggle="tooltip" data-placement="bottom" title="Rerun plugin">
                                    <i className="fa fa-refresh"></i>
                                </button>
                                <button className="btn btn-danger" data-toggle="tooltip" data-placement="bottom" title="Delete plugin output">
                                    <i className="fa fa-times"></i>
                                </button>
                            </div>
                        </td>
                    </tr>
                    <tr>
                        <th colSpan="6">
                            <button className="btn btn-default pull-right">
                                <i className="fa fa-pencil"></i>
                                Notes
                            </button>
                        </th>
                    </tr>
                    <tr>
                        <td colSpan="6">
                            <textarea className="editor" style={{
                                display: "none"
                            }}></textarea>
                        </td>
                    </tr>
                    <tr>
                        <th colSpan="6">
                            MORE DETAILS
                        </th>
                    </tr>
                    <tr>
                        <td colSpan="6" dangerouslySetInnerHTML={{
                            __html: output
                        }}></td>
                    </tr>
                </tbody>
            </table>
        );
    }
}

export default Table;
