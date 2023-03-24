import React, { Component } from "react";
import ReactDOM from "react-dom";

import { IoCloseSharp } from "react-icons/io5";

const modalContainer = document.querySelector("#modalContainer");

export default class Dialog extends Component {
  render() {
    return ReactDOM.createPortal(
      <div>
        {this.props.isDialogOpened ? (
          <div className="dialogContainer">
            <div className="dialogContainer__dialog">
              <div className="dialogContainer__content">
                <div className="dialogContainer__header">
                  <h2 className="dialogContainer__title">{this.props.title}</h2>
                  <button onClick={this.props.onClose}>
                    <IoCloseSharp />
                  </button>
                </div>
                <div className="dialogContainer__body">
                  {this.props.children}
                </div>
              </div>
            </div>
          </div>
        ) : null}
      </div>,
      modalContainer
    );
  }
}
