import React from 'react';
import { Tablist, SidebarTab, Pane, Heading } from 'evergreen-ui';
import PropTypes from 'prop-types';

export default class TargetList extends React.Component {

  constructor(props, context) {
    super(props, context);

    this.renderTargetList = this.renderTargetList.bind(this);

    this.state = {
      selectedIndex: null,
    };
  }

  handleSelect(index, target_id) {
    event.preventDefault();
    this.setState({
      selectedIndex: index
    });
    this.props.getTransactions(target_id);
  }

  renderTargetList() {
    if (this.props.targets !== false) {
      return this.props.targets.map((target, index) => {
        return (
          <SidebarTab
            key={target.id}
            id={target.id}
            onSelect={() => this.handleSelect(index, target.id)}
            isSelected={index === this.state.selectedIndex}
            aria-controls={`panel-${target.id}`}
          >
            {target.target_url}
          </SidebarTab>
        );
      });
    }
  }

  render() {
    return (
      <Pane display="flex" flexDirection="column">
        <Pane>
          <Heading size={700}>Targets</Heading>
        </Pane>
        <Pane display="flex" marginTop={30}>
          <Tablist marginBottom={16} flexBasis={240} marginRight={24} onSelect={k => this.handleSelect(k)}>
            {this.renderTargetList()}
          </Tablist>
        </Pane>
      </Pane>
    );
  }
}

TargetList.propTypes = {
  targets: PropTypes.array,
  getTransactions: PropTypes.func
};
