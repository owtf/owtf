import React, {useState} from 'react';
import { Tablist, SidebarTab, Pane, Heading } from 'evergreen-ui';
import PropTypes from 'prop-types';

interface ITargetListProps{
  targets: Array<any>;
  getTransactions: Function;
}

export default function TargetList(
  {
    targets,
    getTransactions
  }: ITargetListProps
){

  const [selectedIndex, setSelectedIndex] = useState(null);
  
  const handleSelect = (index: number | React.SetStateAction<null>, target_id: any) => {
    event.preventDefault();
    setSelectedIndex(index);
    getTransactions(target_id);
  }

  const renderTargetList = () => {
    if (targets !== false) {
      return targets.map((target, index) => {
        return (
          <SidebarTab
            key={target.id}
            id={target.id}
            onSelect={() => handleSelect(index, target.id)}
            isSelected={index === selectedIndex}
            aria-controls={`panel-${target.id}`}
          >
            {target.target_url}
          </SidebarTab>
        );
      });
    }
  }

  return (
    <>
      <Pane display="flex" flexDirection="column" data-test="targetListComponent">
        <Pane>
          <Heading size={700}>Targets</Heading>
        </Pane>
        <Pane display="flex" marginTop={30}>
          <Tablist marginBottom={16} flexBasis={240} marginRight={24} onSelect={k => this.handleSelect(k)}>
            {renderTargetList()}
          </Tablist>
        </Pane>
      </Pane>
    </>
  );
}

TargetList.propTypes = {
  targets: PropTypes.oneOfType([
    PropTypes.array.isRequired,
    PropTypes.bool.isRequired,
  ]),
  getTransactions: PropTypes.func
};
