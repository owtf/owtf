/**
 * React Component for RankButtons. It is child component used by Collapse Component.
 */

import React from "react";
import { AiTwotoneLike } from 'react-icons/ai';
import { AiFillInfoCircle } from 'react-icons/ai';
import { GoFlame } from 'react-icons/go';
import { MdError } from 'react-icons/md';
import { MdRemoveCircle } from 'react-icons/md';
import { AiFillWarning } from 'react-icons/ai';


interface propTypes {
  obj: object,
  patchUserRank: Function
};



export default class RankButtons extends React.Component <propTypes>{
  render() {
    const { obj, patchUserRank } = this.props;
    const user_rank = obj["user_rank"];
    const owtf_rank = obj["owtf_rank"];
    const group = obj["plugin_group"];
    const type = obj["plugin_type"];
    const code = obj["plugin_code"];
    if (user_rank in [0, 1, 2, 3, 4, 5]) {
      return (
        <div className="targetsCollapse__rankButtonsContainer">
          <button
            style={{ backgroundColor: user_rank === 0 ? "rgba(0, 0, 0, 0.178)" : "transparent" }}
            onClick={() => patchUserRank(group, type, code, 0)}
          >
            <AiTwotoneLike />
          </button>

          <button
            style={{ backgroundColor: user_rank === 1 ? "rgba(0, 0, 0, 0.178)" : "transparent" }}
            onClick={() => patchUserRank(group, type, code, 1)}
          >
            <AiFillInfoCircle />

          </button>


          <button
            style={{ backgroundColor: user_rank === 2 ? "rgba(0, 0, 0, 0.178)" : "transparent" }}
            onClick={() => patchUserRank(group, type, code, 2)}
          >

            <AiFillWarning />
          </button>

          <button
            style={{ backgroundColor: user_rank === 3 ? "rgba(0, 0, 0, 0.178)" : "transparent" }}
            onClick={() => patchUserRank(group, type, code, 3)}
          >
            <MdRemoveCircle />
          </button>


          <button
            style={{ backgroundColor: user_rank === 4 ? "rgba(0, 0, 0, 0.178)" : "transparent" }}
            onClick={() => patchUserRank(group, type, code, 4)}
          >
            <GoFlame />
          </button>

          <button
            style={{ backgroundColor: user_rank === 5 ? "rgba(0, 0, 0, 0.178)" : "transparent" }}
            onClick={() => patchUserRank(group, type, code, 5)}
          >
            <MdError />
          </button>

        </div>
      );
    } else {
      return (
        <div className="targetsCollapse__rankButtonsContainer">
           <button
            style={{ backgroundColor: owtf_rank === 0 ? "rgba(0, 0, 0, 0.178)" : "transparent" }}
            onClick={() => patchUserRank(group, type, code, 0)}
          >
            <AiTwotoneLike />
          </button>

          <button
            style={{ backgroundColor: owtf_rank === 1 ? "rgba(0, 0, 0, 0.178)" : "transparent" }}
            onClick={() => patchUserRank(group, type, code, 1)}
          >
            <AiFillInfoCircle />

          </button>


          <button
            style={{ backgroundColor: owtf_rank === 2 ? "rgba(0, 0, 0, 0.178)" : "transparent" }}
            onClick={() => patchUserRank(group, type, code, 2)}
          >

            <AiFillWarning />
          </button>

          <button
            style={{ backgroundColor: owtf_rank === 3 ? "rgba(0, 0, 0, 0.178)" : "transparent" }}
            onClick={() => patchUserRank(group, type, code, 3)}
          >
            <MdRemoveCircle />
          </button>


          <button
            style={{ backgroundColor: owtf_rank === 4 ? "rgba(0, 0, 0, 0.178)" : "transparent" }}
            onClick={() => patchUserRank(group, type, code, 4)}
          >
            <GoFlame />
          </button>

          <button
            style={{ backgroundColor: owtf_rank === 5 ? "rgba(0, 0, 0, 0.178)" : "transparent" }}
            onClick={() => patchUserRank(group, type, code, 5)}
          >
            <MdError />
          </button>
        
        </div>
      );
    }
  }
}

