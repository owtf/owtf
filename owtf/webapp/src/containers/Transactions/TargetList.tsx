import React from "react";

interface propsType {
  targets: [] | boolean;
  getTransactions: Function;
}
interface stateType {
  selectedIndex: number | string;
}

export default class TargetList extends React.Component<propsType, stateType> {
  constructor(props, context) {
    super(props, context);

    this.renderTargetList = this.renderTargetList.bind(this);

    this.state = {
      selectedIndex: null
    };
  }

  handleSelect(index: any, target_id: number) {
    this.setState({
      selectedIndex: index
    });
    this.props.getTransactions(target_id);
  }

  renderTargetList() {
    if (this.props.targets !== false) {
      //@ts-ignore
      return this.props.targets.map((target, index) => {
        return (
          <div
            className="transactionsPage__targetListContainer__headingAndList__listContainer__listWrapper__listItem"
            key={target.id}
            id={target.id}
            onClick={() => this.handleSelect(index, target.id)}
            style={{
              backgroundColor:
                index === this.state.selectedIndex
                  ? "rgba(36, 156, 255, 0.479)"
                  : ""
            }}
          >
            {target.target_url}
          </div>
        );
      });
    }
  }

  render() {
    return (
      <div
        className="transactionsPage__targetListContainer__headingAndList"
        data-test="targetListComponent"
      >
        <div className="transactionsPage__targetListContainer__headingAndList__headingContainer">
          <h2>Targets</h2>
        </div>
        <div className="transactionsPage__targetListContainer__headingAndList__listContainer">
          <div className="transactionsPage__targetListContainer__headingAndList__listContainer__listWrapper">
            {this.renderTargetList()}
          </div>
        </div>
      </div>
    );
  }
}
