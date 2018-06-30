import React from 'react';
import ReactDOM from 'react-dom';
import { Row, Col } from 'react-bootstrap';
import BootstrapTable from 'react-bootstrap-table-next';
import filterFactory, { textFilter, Comparator } from 'react-bootstrap-table2-filter';
import PropTypes from 'prop-types';
import './style.scss';

const RemoteFilter = ({ data, columns, options, onTableChange, selectRow, rowEvents, rowStyle }) => (
    <BootstrapTable
        remote={{ filter: true }}
        keyField="id"
        data={data}
        columns={columns}
        filter={filterFactory()}
        onTableChange={onTableChange}
        bordered={false}
        selectRow={selectRow}
        rowEvents={rowEvents}
        rowStyle={rowStyle}
    />
);

export default class TransactionTable extends React.Component {

    constructor(props) {
        super(props);

        this.handleMouseMove = this.handleMouseMove.bind(this);
        this.handleTableChange = this.handleTableChange.bind(this);

        this.state = {
            data: this.props.transactions,
            selectedRows: [],
            activeRow: -1,
            resizeTableActive: false,
            tableHeight: 0,
        };
    };

    handleTableChange = (type, { filters }) => {
        setTimeout(() => {
            const result = this.props.transactions.filter((row) => {
                let valid = true;
                for (const dataField in filters) {
                    const { filterVal, filterType, comparator } = filters[dataField];

                    if (filterType === 'TEXT') {
                        if (comparator === Comparator.LIKE) {
                            valid = row[dataField].toString().indexOf(filterVal) > -1;
                        } else {
                            valid = row[dataField] === filterVal;
                        }
                    }
                    if (!valid) break;
                }
                return valid;
            });
            this.setState(() => ({
                data: result
            }));
            this.props.updateHeaderData();
        }, 100);
    }


    /**
      * Function responsible for
      * 1) When zest is not active, updating Header and Body when some row is clicked
      * 2) When zest is active, this function manage multi selection of rows and immediately updates selected row in zest (parentstate) that we will going to be used by requestSender to form zest script
      * 3) handle click is called onRowSelection(material-ui default)
      */
    handleOnClick = (selectedRow) => {
        if (!this.props.zestActive) {
            this.setState(() => ({
                activeRow: selectedRow
            }));
            const transaction_id = this.props.transactions[selectedRow].id;
            const target_id = this.props.target_id;
            /* To update header and body for selected row */
            this.props.getTransactionsHeaders(target_id, transaction_id);
        }
    };

    handleOnSelect = (row, isSelect) => {
        if (isSelect) {
            this.setState(() => ({
                selectedRows: [...this.state.selectedRows, row.id]
            }));
        } else {
            this.setState(() => ({
                selectedRows: this.state.selectedRows.filter(x => x !== row.id)
            }));
        }
        this.props.updateSelectedRowsInZest(selectedRows);
    }

    handleOnSelectAll = (isSelect, rows) => {
        const ids = rows.map(r => r.id);
        if (isSelect) {
            this.setState(() => ({
                selectedRows: ids
            }));
        } else {
            this.setState(() => ({
                selectedRows: []
            }));
        }
        this.props.updateSelectedRowsInZest(this.state.selectedRows);
    }

    componentDidMount() {
        document.addEventListener('mousemove', this.handleMouseMove);
        document.addEventListener('mouseup', e => this.handleMouseUp(e));
        const tablePos = ReactDOM.findDOMNode(this.refs['table'])
            .getBoundingClientRect()
        this.setState({
            tableHeight: (window.innerHeight - tablePos.top) / 2
        });
    };

    componentWillUnmount() {
        document.removeEventListener('mousemove', this.handleMouseMove);
        document.removeEventListener('mouseup', e => this.handleMouseUp(e));

    };

    handleMouseDown(e) {
        this.setState({ resizeTableActive: true });
    };

    handleMouseUp(e) {
        this.setState({ resizeTableActive: false });
    };

    handleMouseMove(e) {
        if (!this.state.resizeTableActive) {
            return;
        }

        const tablePos = ReactDOM.findDOMNode(this.refs['table'])
            .getBoundingClientRect()
        this.setState({
            tableHeight: e.clientY - tablePos.top
        });

        this.props.handleHeaderContainerHeight(window.innerHeight - e.clientY);
    };

    render() {
        const { zestActive, getTransactionsHeaders, target_id, transactions } = this.props;
        const columns = [{
            dataField: 'url',
            text: '',
            filter: textFilter({
                placeholder: 'URL',
                style: {
                    width: '300px',
                }
            }),
            headerStyle: {
                width: '600px'
            }
        }, {
            dataField: 'method',
            text: '',
            filter: textFilter({
                placeholder: 'Method'
            }),
            headerStyle: {
                width: '100px'
            }
        }, {
            dataField: 'response_status',
            text: '',
            filter: textFilter({
                placeholder: 'Status'
            })
        }, {
            dataField: 'time_human',
            text: 'Duration'
        }, {
            dataField: 'local_timestamp',
            text: 'Time'
        }];

        const selectRow = {
            mode: 'checkbox',
            clickToSelect: false,
            hideSelectColumn: !zestActive,
            selected: this.state.selectedRows,
            onSelect: this.handleOnSelect,
            onSelectAll: this.handleOnSelectAll
        };

        const rowEvents = {
            onClick: (e, row, rowIndex) => {
                this.handleOnClick(rowIndex);
            }
        };

        const rowStyle = (row, rowIndex) => {
            const style = {};
            style.cursor = "pointer";
            if (rowIndex === this.state.activeRow) {
                style.backgroundColor = '#c8e6c9';
            }
            return style;
        };

        return (
            <Row>
                <Col ref="table" style={{
                    "height": this.state.tableHeight,
                    "overflow": "scroll"
                }}>
                    <RemoteFilter
                        data={this.state.data}
                        columns={columns}
                        onTableChange={this.handleTableChange}
                        selectRow={selectRow}
                        rowEvents={rowEvents}
                        rowStyle={rowStyle}
                    />
                </Col>
                <Col
                    id="drag"
                    onMouseDown={e => this.handleMouseDown(e)}
                    onMouseUp={e => this.handleMouseUp(e)}
                />
            </Row>
        );
    }
}

TransactionTable.PropTypes = {
    target_id: PropTypes.number,
    transactions: PropTypes.array,
    zestActive: PropTypes.bool,
    getTransactionsHeaders: PropTypes.func,
    handleHeaderContainerHeight: PropTypes.func,
    updateSelectedRowsInZest: PropTypes.func,
    updateHeaderData: PropTypes.func,
};