import React from 'react';
import Input from 'react-toolbox/lib/input';

import {
    Table,
    TableBody,
    TableHeader,
    TableHeaderColumn,
    TableRow,
    TableRowColumn
} from 'material-ui/Table';

export class TransactionTable extends React.Component {

    constructor(props) {
        super(props);
        this.state = {
            selectedRowsArray: [],
            resizeTableActive: false,
            tableHeight: 0
        };

        this.handleMouseMove = this.handleMouseMove.bind(this);
    };

    /* Function responsible for
    1) When zest is not active, updating Header and Body when some row is clicked
    2) When zest is active, this function manage multi selection of rows and immediately updates
       selected row in zest (parentstate) that we will going to be used by requestSender to form zest script
    3) handle click is called onRowSelection(material-ui default)*/
    handleClick(selectedRows) {
        if (selectedRows === 'all') {
            var N = this.context.transactionsData.length;
            selectedRows = Array.apply(null, {length: N}).map(Number.call, Number);
        } else if (selectedRows === 'none') {
            selectedRows = [];
        }
        this.setState({selectedRowsArray: selectedRows});
        if (!this.context.zestActive) {
            var transaction_id = this.context.transactionsData[selectedRows[0]].id;
            var target_id = this.context.target_id;
            /* To update header and body for selected row */
            this.context.getTransactionsHeaders(target_id, transaction_id);
        } else {
            /* To update the selcted row in zest */
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
        var selectedRowsArray = this.state.selectedRowsArray;
        var zestActive = this.context.zestActive;
        return (
            <div>
                {/*<p style={{
                    display: "inline"
                }}>Show</p>
                <DropDownMenu value={this.context.limitValue} onChange={this.context.handleLimitChange} disabled={this.context.target_id === 0}>
                    <MenuItem value={25} primaryText="25"/>
                    <MenuItem value={50} primaryText="50"/>
                    <MenuItem value={75} primaryText="75"/>
                    <MenuItem value={100} primaryText="100"/>
                </DropDownMenu>
                <p style={{
                    display: "inline"
                }}>entries</p>*/}
                <Table height={this.state.tableHeight} onRowSelection={this.handleClick.bind(this)} multiSelectable={this.context.zestActive}>
                    <TableHeader adjustForCheckbox={this.context.zestActive} displaySelectAll={this.context.zestActive}>
                        <TableRow>
                            <TableHeaderColumn>
                                <Input type='text' label='URL' onChange={e => this.context.tableSearch(e, "url")}/>
                            </TableHeaderColumn>
                            <TableHeaderColumn style={{
                                width: 120
                            }}>
                                <Input type='text' label='Method' onChange={e => this.context.tableSearch(e, "method")}/>
                            </TableHeaderColumn>
                            <TableHeaderColumn style={{
                                width: 200
                            }}>
                                <Input type='text' label='Status' onChange={e => this.context.tableSearch(e, "status")}/>
                            </TableHeaderColumn>
                            <TableHeaderColumn style={{
                                width: 120
                            }}>Duration</TableHeaderColumn>
                            <TableHeaderColumn style={{
                                width: 150
                            }}>Time</TableHeaderColumn>
                        </TableRow>
                    </TableHeader>
                    <TableBody displayRowCheckbox={this.context.zestActive} deselectOnClickaway={false}>
                        {this.context.transactionsData.map(function(transaction, index) {
                            return (
                                <TableRow key={index} selected={(selectedRowsArray.indexOf(index) !== -1)} style={{
                                    cursor: "pointer"
                                }}>
                                    <TableRowColumn>{transaction.url}</TableRowColumn>
                                    <TableRowColumn style={{
                                        width: 120
                                    }}>{transaction.method}</TableRowColumn>
                                    <TableRowColumn style={{
                                        width: 200
                                    }}>{transaction.response_status}</TableRowColumn>
                                    <TableRowColumn style={{
                                        width: 120
                                    }}>{transaction.time_human}</TableRowColumn>
                                    <TableRowColumn style={{
                                        width: 150
                                    }}>{transaction.local_timestamp}</TableRowColumn>
                                </TableRow>
                            );
                        })}
                    </TableBody>
                </Table>
                <div id="drag" onMouseDown={e => this.handleMouseDown(e)} onMouseUp={e => this.handleMouseUp(e)}></div>
                {/* Imp: Interesting logical operators are used to determine when to show pagination and when not :)
                    If A = this.context.transactionsData.length !== 0
                    If B = this.context.offsetValue == 0, then
                    This transition table should the case to decide when to show pagination and when not
                    ---------------------
                    |  A  | B  | result |
                    |-------------------|
                    |  T  | T  |   T    |
                    |  T  | F  |   T    |
                    |  F  | T  |   F    |
                    |  F  | F  |   T    |
                    ---------------------
                    General Answer should be = ((true AND NOT(B)) OR A)


                {(true && !(this.context.offsetValue == 0)) || (this.context.transactionsData.length !== 0)
                    ? <Pagination nextDisabled={this.context.transactionsData.length === 0} previousDisabled={this.context.offsetValue == 0}/>
                    : null}
                */}
            </div>
        );
    }
}

TransactionTable.contextTypes = {
    muiTheme: React.PropTypes.object.isRequired,
    target_id: React.PropTypes.number,
    limitValue: React.PropTypes.number,
    offsetValue: React.PropTypes.number,
    transactionsData: React.PropTypes.array,
    zestActive: React.PropTypes.bool,
    getTransactionsHeaders: React.PropTypes.func,
    handleLimitChange: React.PropTypes.func,
    handleOffsetChange: React.PropTypes.func,
    getElementTopPosition: React.PropTypes.func,
    handleHeaderContainerHeight: React.PropTypes.func,
    updateSelectedRowsInZest: React.PropTypes.func,
    tableSearch: React.PropTypes.func
};

export default TransactionTable;
