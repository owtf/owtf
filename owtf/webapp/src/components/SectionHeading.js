import React from 'react';
import styled from 'styled-components';

export default styled(({label, ...props}) => {
  return (
    <div {...props}>
      {props.children}
    </div>
  );
})`
  font-size: 16px;
  font-weight: 500;
  text-transform: uppercase;
  margin: 0 0 20px;
  letter-spacing: -1px;
  color: #111;
`;