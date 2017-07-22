import React from 'react';

const styles = {
    tab: {
        paddingTop: 16,
        marginBottom: 12,
        fontWeight: 400
    },
    button: {
        marginLeft: "5px"
    }
};

/**
 *  React Component for GitHubReport(Top right button).
 *  It is child components which is used by Dashboard.js
 *  Uses Rest API - /api/errors/ (Obtained from props)
 */

class GitHubReport extends React.Component {

    constructor(props) {
        super(props);

        this.state = {
            errorData: []
        }

        this.addGithubIssue = this.addGithubIssue.bind(this);
        this.openGitHubIssue = this.openGitHubIssue.bind(this);
        this.deleteIssue = this.deleteIssue.bind(this);
    };

    /**
     * Function resposible to submit github issue.
     * Rest API - /api/errors/
     * @param {id, e} values id: id of error to submit, e: DOM event
     */

    addGithubIssue(id, e) {
        e.preventDefault();
        var username = $('#error' + id.toString() + "-username").val();
        var title = $('#error' + id.toString() + "-title").val();
        var body = $('#error' + id.toString() + "-body").val();
        var data = {
            id: id,
            username: username,
            title: title,
            body: body
        };
        $.ajax({
            async: false,
            url: this.props.source,
            type: 'POST',
            dataType: 'json',
            data: data,
            success: function(data) {
                if (data.message) {
                    $("#error" + id.toString() + "-showerror").html(data.message);
                } else {
                    $.get(this.props.source, function(result) {
                        this.setState({errorData: result});
                    }.bind(this));
                }
            }.bind(this),
            error: function(xhr, status, err) {
                $("#error" + id.toString() + "-showerror").html(err.toString());
            }.bind(this)
        });
    };

    /* Function resposible to open github issue */
    openGitHubIssue(link) {
        window.open(link);
    };

    /**
     * Function resposible to delete a error from OWTF database.
     * Rest API - /api/errors/
     * @param {id} values id: id of error to submit.
     */

    deleteIssue(id) {
        $.ajax({
            url: this.props.source + id.toString(),
            type: 'DELETE',
            success: function(data) {
                $.get(this.props.source, function(result) {
                    this.setState({errorData: result});
                }.bind(this));
            }.bind(this)
        });
    };

    /* Making an AJAX request on source property */
    componentDidMount() {
        this.serverRequest = $.get(this.props.source, function(result) {
            this.setState({errorData: result});
        }.bind(this));
    };

    componentWillUnmount() {
        this.serverRequest.abort();
    };

    render() {
        var addGithubIssue = this.addGithubIssue;
        var openGitHubIssue = this.openGitHubIssue;
        var deleteIssue = this.deleteIssue;
        return (
            <div>
                <button type="button" className="btn btn-danger center-block" data-toggle="modal" data-target="#errorModal">
                    <i className="fa fa-github" aria-hidden="true"></i>
                    &nbsp;Report Errors on GitHub
                </button>
                {/* Modal to show Errors */}
                <div className="modal fade" id="errorModal" tabindex="-1" role="dialog" aria-labelledby="myModalLabel">
                    <div className="modal-dialog" role="document">
                        <div className="modal-content">
                            <div className="modal-header">
                                <button type="button" className="close" data-dismiss="modal" aria-label="Close">
                                    <span aria-hidden="true">&times;</span>
                                </button>
                                <h4 className="modal-title">Errors</h4>
                            </div>
                            <div className="modal-body" id="error-modal-body">
                                <ul className="nav nav-tabs" style={styles.tab}>
                                    {this.state.errorData.map(function(error, index) {
                                        return (
                                            <li className={index === 0
                                                ? "active"
                                                : ""}>
                                                <a href={"#error" + error.id} data-toggle="tab">{"Error " + error.id}</a>
                                            </li>
                                        );
                                    })}
                                </ul>
                                {/* Show tab content on basis of reported status */}
                                <div className="tab-content">
                                    {this.state.errorData.map(function(error, index) {
                                        return (
                                            <div className={index === 0
                                                ? "tab-pane active"
                                                : "tab-pane"} id={"error" + error.id}>
                                                {error.reported
                                                    ? <div>
                                                            <p className="error-modal-body-title">Issue is reported on github with following body</p>
                                                            <label>Body*</label>
                                                            <textarea id={"error" + error.id + "-body"} className="form-control" rows="6" value={error.traceback} disabled></textarea>
                                                            <br/>
                                                            <div className="inline pull-right">
                                                                <button type="button" className="btn navbar-btn btn-primary text-center" onClick={openGitHubIssue.bind(this, error.github_issue_url)}>
                                                                    <i className="fa fa-github" aria-hidden="true"></i>
                                                                    &nbsp;Show issue on GitHub
                                                                </button>
                                                                <button type="button" className="btn navbar-btn btn-danger text-center" onClick={deleteIssue.bind(this, error.id)} style={styles.button}>
                                                                    <i className="fa fa-trash-o" aria-hidden="true"></i>
                                                                    &nbsp;Delete error
                                                                </button>
                                                            </div>
                                                        </div>
                                                    : <form onSubmit={addGithubIssue.bind(this, error.id)}>
                                                        <p className="error-modal-body-title" id={"error" + error.id + "-showerror"}></p>
                                                        <div className="form-group">
                                                            <label>Your Github Username*</label>
                                                            <input id={"error" + error.id + "-username"} type="text" required="required" className="form-control" placeholder="GitHub username"/>
                                                            <br/>
                                                            <label>Title*</label>
                                                            <input id={"error" + error.id + "-title"} type="text" className="form-control" placeholder="Title" value="[Auto-Generated] Bug report from OWTF"/>
                                                            <br/>
                                                            <label>Body*</label>
                                                            <textarea id={"error" + error.id + "-body"} className="form-control" rows="6" value={"#### OWTF Bug Report\n\n" + error.traceback}></textarea>
                                                        </div>
                                                        <div className="inline pull-right">
                                                            <input type="submit" className="btn btn-success" value="Create issue on GitHub"/>
                                                            <button type="button" className="btn btn-danger" onClick={deleteIssue.bind(this, error.id)} style={styles.button}>
                                                                <i className="fa fa-trash-o" aria-hidden="true"></i>
                                                                &nbsp;Delete error
                                                            </button>
                                                        </div>
                                                    </form>
                                                  }
                                            </div>
                                        );
                                    })}
                                </div>
                                <p>
                                    {this.state.errorData.length === 0
                                        ? "Currently no errors exists"
                                        : ""}
                                </p>
                            </div>
                            <div className="modal-footer">
                                <button type="button" className="btn btn-default" data-dismiss="modal">Close</button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        );
    }
}

export default GitHubReport;
