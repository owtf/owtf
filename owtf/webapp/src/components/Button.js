import {Link} from 'react-router';
import styled, {css} from 'styled-components';

// TODO(dcramer): how do we avoid copy pasta?
export const ButtonLink = styled(Link)`
  background: #7b6be6;
  color: #fff;
  display: inline-block;
  border: 2px solid #7b6be6;
  border-radius: 3px;
  cursor: pointer;
  font-weight: 500;

  ${props => {
    switch (props.type) {
      case 'danger':
        return css`
          background: #fff;
          color: #e03e2f;
          border-color: #e03e2f;
        `;
      case 'primary':
        return css`
          background: #fff;
          color: #7b6be6;
          border-color: #7b6be6;
        `;
      case 'light':
        return css`
          background: #fff;
          color: #666;
          border-color: #eee;
        `;
      default:
        return css`
          background: #fff;
          color: #111;
          border-color: #111;
        `;
    }
  }};

  ${props => {
    switch (props.size) {
      case 'xs':
        return css`
          font-size: 9px;
          padding: 2px 4px;
        `;
      case 'small':
        return css`
          font-size: 12px;
          padding: 4px 8px;
        `;
      case 'large':
        return css`
          font-size: 16px;
          padding: 8px 12px;
        `;
      default:
        return css`
          font-size: 14px;
          padding: 8px 12px;
        `;
    }
  }};

  ${props =>
    props.disabled &&
    `
      cursor: default;
      opacity: 0.3;
    `};
`;

export default styled.a`
  background: #7b6be6;
  color: #fff;
  display: inline-block;
  border: 2px solid #7b6be6;
  border-radius: 3px;
  cursor: pointer;
  font-weight: 500;

  ${props => {
    switch (props.type) {
      case 'danger':
        return css`
          background: #fff;
          color: #e03e2f;
          border-color: #e03e2f;
        `;
      case 'primary':
        return css`
          background: #fff;
          color: #7b6be6;
          border-color: #7b6be6;
        `;
      case 'light':
        return css`
          background: #fff;
          color: #999;
          border-color: #eee;
        `;
      default:
        return css`
          background: #fff;
          color: #111;
          border-color: #111;
        `;
    }
  }};

  ${props => {
    switch (props.size) {
      case 'xs':
        return css`
          font-size: 9px;
          padding: 2px 4px;
        `;
      case 'small':
        return css`
          font-size: 12px;
          padding: 4px 8px;
        `;
      case 'large':
        return css`
          font-size: 16px;
          padding: 8px 12px;
        `;
      default:
        return css`
          font-size: 14px;
          padding: 8px 12px;
        `;
    }
  }};

  ${props =>
    props.disabled &&
    `
      cursor: default;
      opacity: 0.3;
    `};
`;