/**
 * React Component for RankButtons. It is child component used by Collapse Component.
 */

import React from "react";
import { Pane, IconButton } from "evergreen-ui";
import PropTypes from "prop-types";

export default class RankButtons extends React.Component {
  render() {
    const { obj, patchUserRank } = this.props;
    const user_rank = obj["user_rank"];
    const owtf_rank = obj["owtf_rank"];
    const group = obj["plugin_group"];
    const type = obj["plugin_type"];
    const code = obj["plugin_code"];
    if (user_rank in [0, 1, 2, 3, 4, 5]) {
      return (
        <Pane display="flex" flexDirection="row">
          <IconButton
            appearance={user_rank === 0 ? "primary" : "default"}
            intent={user_rank === 0 ? "success" : "none"}
            isActive={user_rank === 0 ? true : false}
            icon="thumbs-up"
            onClick={() => patchUserRank(group, type, code, 0)}
            borderRadius={0}
          />
          <IconButton
            appearance={user_rank === 1 ? "primary" : "default"}
            intent={user_rank === 1 ? "success" : "none"}
            isActive={user_rank === 1 ? true : false}
            icon="info-sign"
            onClick={() => patchUserRank(group, type, code, 1)}
            borderRadius={0}
          />
          <IconButton
            appearance={user_rank === 2 ? "primary" : "default"}
            intent={user_rank === 2 ? "warning" : "none"}
            isActive={user_rank === 2 ? true : false}
            icon="warning-sign"
            onClick={() => patchUserRank(group, type, code, 2)}
            borderRadius={0}
          />
          <IconButton
            appearance={user_rank === 3 ? "primary" : "default"}
            intent={user_rank === 3 ? "warning" : "none"}
            isActive={user_rank === 3 ? true : false}
            icon="ban-circle"
            onClick={() => patchUserRank(group, type, code, 3)}
            borderRadius={0}
          />
          <IconButton
            appearance={user_rank === 4 ? "primary" : "default"}
            intent={user_rank === 4 ? "danger" : "none"}
            isActive={user_rank === 4 ? true : false}
            icon="flame"
            onClick={() => patchUserRank(group, type, code, 4)}
            borderRadius={0}
          />
          <IconButton
            appearance={user_rank === 5 ? "primary" : "default"}
            intent={user_rank === 5 ? "danger" : "none"}
            isActive={user_rank === 5 ? true : false}
            icon="error"
            onClick={() => patchUserRank(group, type, code, 5)}
            borderRadius={0}
          />
        </Pane>
      );
    } else {
      return (
        <Pane display="flex" flexDirection="row">
          <IconButton
            appearance={owtf_rank === 0 ? "primary" : "default"}
            intent={owtf_rank === 0 ? "success" : "none"}
            isActive={owtf_rank === 0 ? true : false}
            icon="thumbs-up"
            onClick={() => patchUserRank(group, type, code, 0)}
            borderRadius={0}
          />
          <IconButton
            appearance={owtf_rank === 1 ? "primary" : "default"}
            intent={owtf_rank === 1 ? "success" : "none"}
            isActive={owtf_rank === 1 ? true : false}
            icon="info-sign"
            onClick={() => patchUserRank(group, type, code, 1)}
            borderRadius={0}
          />
          <IconButton
            appearance={owtf_rank === 2 ? "primary" : "default"}
            intent={owtf_rank === 2 ? "warning" : "none"}
            isActive={owtf_rank === 2 ? true : false}
            icon="warning-sign"
            onClick={() => patchUserRank(group, type, code, 2)}
            borderRadius={0}
          />
          <IconButton
            appearance={owtf_rank === 3 ? "primary" : "default"}
            intent={owtf_rank === 3 ? "warning" : "none"}
            isActive={owtf_rank === 3 ? true : false}
            icon="ban-circle"
            onClick={() => patchUserRank(group, type, code, 3)}
            borderRadius={0}
          />
          <IconButton
            appearance={owtf_rank === 4 ? "primary" : "default"}
            intent={owtf_rank === 4 ? "danger" : "none"}
            isActive={owtf_rank === 4 ? true : false}
            icon="flame"
            onClick={() => patchUserRank(group, type, code, 4)}
            borderRadius={0}
          />
          <IconButton
            appearance={owtf_rank === 5 ? "primary" : "default"}
            intent={owtf_rank === 5 ? "danger" : "none"}
            isActive={owtf_rank === 5 ? true : false}
            icon="error"
            onClick={() => patchUserRank(group, type, code, 5)}
            borderRadius={0}
          />
        </Pane>
      );
    }
  }
}

RankButtons.propTypes = {
  obj: PropTypes.object,
  patchUserRank: PropTypes.func
};
