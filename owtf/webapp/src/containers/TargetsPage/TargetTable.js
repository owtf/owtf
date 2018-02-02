import React from 'react';
import BootstrapTable from 'react-bootstrap-table-next';
import { Row, Col } from 'react-flexbox-grid';

import { Label } from 'react-bootstrap';


function severityFormatter(cell, row, rowIndex, formatExtraData) {
  const type = {
	  "Passing": "primary",
	  "High": "danger"
  }
  let t = Object.keys(formatExtraData).find(key => formatExtraData[key] === cell);
  return (
	<Label bsStyle={t}>{cell}</Label>
  );
}

export default class TargetTable extends React.Component {
	render() {
		const columns = [{
			dataField: 'target',
			text: 'Target'
			}, {
			dataField: 'severity',
			text: 'Severity',
			formatter: severityFormatter,
  			formatExtraData: {
    			primary: "Passing",
    			danger: "High"
			}
		}];

		const targets = [{
			id: '1',
			target: 'www.google.com',
			severity: 'Passing'
			}, {
			id: '2',
			target: 'google.com',
			severity: 'Passing'
		}];

		const selectRow = {
			mode: 'checkbox',
			clickToSelect: true,
			style: { backgroundColor: '#c8e6c9' }
		};

		return (
			<BootstrapTable
			keyField='id'
			data={targets}
			columns={columns}
			selectRow={selectRow}
			/>
		);
	}
}