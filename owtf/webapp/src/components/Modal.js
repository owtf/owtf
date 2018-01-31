import React, {Component} from 'react';
import PropTypes from 'prop-types';


export default class Modal extends Component {
  static propTypes = {
    title: PropTypes.string.isRequired,
    subtext: PropTypes.string,
    maxWidth: PropTypes.number
  };

  static defaultProps = {
    maxWidth: 600
  };

  render() {
    return (
      <div
        style={{
        margin: 'auto',
        maxWidth: this.props.maxWidth
      }}>
        <div style={{
          textAlign: 'center',
          marginTop: 20
        }}>
        </div>
        <div
          style={{
          border: '10px solid #111',
          margin: 20,
          borderRadius: '4px',
          padding: 20
        }}>
          {this.props.subtext
            ? (
              <h1
                style={{
                opacity: 0.2,
                float: 'right'
              }}>{this.props.subtext}</h1>
            )
            : null}
          <h1>{this.props.title}</h1>
          {this.props.children}
        </div>
        <div
          style={{
          textAlign: 'center',
          color: '#333',
          fontSize: '0.8em'
        }}>
          <a
            href="https://github.com/owtf/owtf"
            style={{
            color: 'inherit',
            fontWeight: 500
          }}>
            OWTF
          </a>{' '}
          is Open Source Software
        </div>
      </div>
    );
  }
}