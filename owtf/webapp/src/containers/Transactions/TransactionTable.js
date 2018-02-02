import React from 'react';

/**
  * React Component for TransactionTable. It is child component used by Transactions.
  */

export class TransactionTable extends React.Component {

    constructor(props) {
        super(props);
        this.state = {
            resizeTableActive: false,
            tableHeight: 0
        };

        this.handleMouseMove = this.handleMouseMove.bind(this);
        this.handleClick = this.handleClick.bind(this);
        this.handleRowSelection = this.handleRowSelection.bind(this);
    };

    /**
      * Function responsible for
      * 1) When zest is not active, updating Header and Body when some row is clicked
      * 2) When zest is active, this function manage multi selection of rows and immediately updates selected row in zest (parentstate) that we will going to be used by requestSender to form zest script
      * 3) handle click is called onRowSelection(material-ui default)
      */
    handleClick(selectedRows, e) {
        if (!this.context.zestActive) {
            $(e.target).parent().addClass('active').siblings().removeClass('active');
            var transaction_id = this.context.transactionsData[selectedRows].id;
            var target_id = this.context.target_id;
            /* To update header and body for selected row */
            this.context.getTransactionsHeaders(target_id, transaction_id);
        }
    };

    /**
      * Function responsible for handling selection of checkboxes when zest is Active.
      */

    handleRowSelection(index, e) {
        if (this.context.zestActive) {
            var selectedRows = [];
            var checkboxes = $('input.table_checkbox');
            if (index === "-1") {
                for (var i = 1; i < checkboxes.length; i++) {
                    checkboxes[i].checked = checkboxes[0].checked;
                }
            };

            for (var i = 1; i < checkboxes.length; i++) {
                if (checkboxes[i].checked) {
                    selectedRows.push(i - 1);
                }
            }
            this.context.updateSelectedRowsInZest(selectedRows);
        }
    };

    componentDidMount() {
        document.addEventListener('mousemove', this.handleMouseMove);
        var tableBody = document.getElementsByTagName("tbody")[0];
        this.setState({
            tableHeight: (window.innerHeight - this.context.getElementTopPosition(tableBody)) / 2
        });
    };

    componentWillUnmount() {
        document.removeEventListener('mousemove', this.handleMouseMove);
    };

    handleMouseDown(e) {
        this.setState({resizeTableActive: true});
    };

    handleMouseUp(e) {
        this.setState({resizeTableActive: false});
    };

    handleMouseMove(e) {
        if (!this.state.resizeTableActive) {
            return;
        }

        var tableBody = document.getElementsByTagName("tbody")[0];
        this.setState({
            tableHeight: e.clientY - this.context.getElementTopPosition(tableBody)
        });

        this.context.handleHeaderContainerHeight(window.innerHeight - e.clientY);
    };

    render() {
        var zestActive = this.context.zestActive;
        var handleClick = this.handleClick;
        var handleRowSelection = this.handleRowSelection;
        return (
            <div>
                <table className="table table-striped">
                    <thead>
                        <tr>
                            <th style={zestActive
                                ? {
                                    width: "1%"
                                }
                                : {
                                    width: "1%",
                                    display: "none"
                                }}>
                                <input name="all" className="table_checkbox" type="checkbox" onChange={handleRowSelection.bind(this, "-1")}/>
                            </th>
                            <th className="col-md-6">
                                <div className="input-group">
                                    <input type="text" className="form-control" placeholder="URL" onChange={e => this.context.tableSearch(e, "url")}/>
                                </div>
                            </th>
                            <th className="col-md-1">
                                <div className="input-group">
                                    <input type="text" className="form-control" placeholder="Method" onChange={e => this.context.tableSearch(e, "method")}/>
                                </div>
                            </th>
                            <th className="col-md-2">
                                <div className="input-group">
                                    <input type="text" className="form-control" placeholder="Status" onChange={e => this.context.tableSearch(e, "status")}/>
                                </div>
                            </th>
                            <th className="col-md-1">Duration</th>
                            <th className="col-md-1">Time</th>
                        </tr>
                    </thead>
                </table>
                <div style={{
                    "height": this.state.tableHeight,
                    "overflow": "scroll"
                }}>
                    <table className="table">
                        <tbody>
                            {this.context.transactionsData.map(function(transaction, index) {
                                return (
                                    <tr key={index} onClick={handleClick.bind(this, index)} style={{
                                        cursor: "pointer"
                                    }}>
                                        <td style={zestActive
                                            ? {
                                                width: "1%"
                                            }
                                            : {
                                                width: "1%",
                                                display: "none"
                                            }}>
                                            <input className="table_checkbox" type="checkbox" onChange={handleRowSelection.bind(this, index)} name={index}/>
                                        </td>
                                        <td className="col-md-6">{transaction.url}</td>
                                        <td className="col-md-1">{transaction.method}</td>
                                        <td className="col-md-2">{transaction.response_status}</td>
                                        <td className="col-md-1">{transaction.time_human}</td>
                                        <td className="col-md-1">{transaction.local_timestamp}</td>
                                    </tr>
                                );
                            })}
                        </tbody>
                    </table>
                </div>
                <div id="drag" onMouseDown={e => this.handleMouseDown(e)} onMouseUp={e => this.handleMouseUp(e)}></div>
            </div>
        );
    }
}

TransactionTable.contextTypes = {
    //target_id: React.PropTypes.number,
    // limitValue: React.PropTypes.number,
    // offsetValue: React.PropTypes.number,
    // transactionsData: React.PropTypes.array,
    // zestActive: React.PropTypes.bool,
    // getTransactionsHeaders: React.PropTypes.func,
    // handleLimitChange: React.PropTypes.func,
    // handleOffsetChange: React.PropTypes.func,
    // getElementTopPosition: React.PropTypes.func,
    // handleHeaderContainerHeight: React.PropTypes.func,
    // updateSelectedRowsInZest: React.PropTypes.func,
    // tableSearch: React.PropTypes.func
};

export default TransactionTable;
