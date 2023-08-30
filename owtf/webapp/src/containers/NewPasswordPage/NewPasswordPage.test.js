import React from "react";
import { shallow } from "enzyme";
import toJson from "enzyme-to-json";
import "../../setupTests";
import { findByTestAtrr, checkProps } from "../../utils/testUtils";
import { NewPasswordPage } from "./index";
import { fromJS } from "immutable";

import { newPasswordFail, newPasswordSuccess } from "./actions";
import {
  NEW_PASSWORD_START,
  NEW_PASSWORD_SUCCESS,
  NEW_PASSWORD_FAIL
} from "./constants";

import { postDataToNewPasswordAPI } from "./saga";
import { runSaga } from "redux-saga";
import * as api from "./api";

import { NewPasswordReducer } from "./reducer";

describe("NewPasswordPage component", () => {
  describe("Testing dumb new password page component", () => {
    let wrapper;
    let props;
    beforeEach(() => {
      props = {
        onNewPassword: jest.fn(),
        otp: "123456",
        emailOrUsername: "test_user@test.com"
      };
      wrapper = shallow(<NewPasswordPage {...props} />);
    });
    it("Should have correct prop-types", () => {
      const expectedProps = {
        onNewPassword: () => {},
        otp: "123456",
        email: "test_user@test.com"
      };
      const propsErr = checkProps(NewPasswordPage, expectedProps);
      expect(propsErr).toBeUndefined();
    });

    it("Should render without errors", () => {
      const component = findByTestAtrr(wrapper, "newPasswordPageComponent");
      expect(component.length).toBe(1);
      expect(toJson(component)).toMatchSnapshot();
    });

    it("Should correctly render its sub-components", () => {
      wrapper.setState({
        newPassword: "Test@1234",
        newConfirmPassword: "Test@1234",
        errors: {},
        hidePassword: true,
        hideConfirmPassword: true
      });
      const pane = wrapper.find("div");
      const heading = wrapper.find("h2");
      const textInputField = wrapper.find("input");
      const paragraph = wrapper.find("p");
      const button = wrapper.find("button");

      expect(pane.length).toBe(5);
      expect(heading.length).toBe(1);
      expect(heading.at(0).props().children).toEqual("Reset Password");
      expect(textInputField.length).toBe(2);
      expect(paragraph.length).toBe(3);
      expect(paragraph.at(0).props().children).toEqual(
        "Your current password has expired. Please create a new password."
      );
      expect(button.length).toBe(1);
      expect(button.at(0).props().children).toEqual("Change Password");
    });

    it("Should call onNewPassword on resend link click", () => {
      expect(props.onNewPassword.mock.calls.length).toBe(0);
      const resendButton = wrapper.find("button");
      resendButton.simulate("click");
      expect(props.onNewPassword.mock.calls.length).toBe(1);
    });
  });

  describe("Testing the sagas", () => {
    describe("Testing postDataToNewPasswordAPI saga", () => {
      let fakeAction;
      beforeEach(() => {
        fakeAction = {
          type: NEW_PASSWORD_START,
          emailOrUsername: "test_user@test.com",
          otp: 123456,
          password: "Test@1234"
        };
      });

      it("Should create a new password in case of success", async () => {
        const emailOrUsername = "test_user@test.com";
        const successData = {
          status: "success",
          data: { status: "success", message: "Password Change Successful" }
        };

        const dispatchedActions = [];
        api.newPasswordAPI = jest.fn(() =>
          jest.fn(() => Promise.resolve(successData))
        );

        const fakeStore = {
          getState: () => ({ state: "test" }),
          dispatch: action => dispatchedActions.push(action)
        };

        await runSaga(fakeStore, postDataToNewPasswordAPI, fakeAction).done;
        expect(api.newPasswordAPI.mock.calls.length).toBe(1);
        expect(dispatchedActions).toContainEqual(
          newPasswordSuccess(successData["data"]["message"], emailOrUsername)
        );
      });

      it("Should handle new password error in case of failure", async () => {
        const dispatchedActions = [];
        const error = "API server is down";
        api.newPasswordAPI = jest.fn(() =>
          jest.fn(() => Promise.reject(error))
        );

        const fakeStore = {
          getState: () => ({ state: "test" }),
          dispatch: action => dispatchedActions.push(action)
        };

        await runSaga(fakeStore, postDataToNewPasswordAPI, fakeAction).done;
        expect(api.newPasswordAPI.mock.calls.length).toBe(1);
        expect(dispatchedActions).toContainEqual(newPasswordFail(error));
      });
    });
  });

  describe("Testing reducers", () => {
    describe("Testing NewPasswordReducer", () => {
      let initialState;
      beforeEach(() => {
        initialState = {
          error: false,
          loading: false
        };
      });

      it("Should return the initial state", () => {
        const newState = NewPasswordReducer(undefined, {});
        expect(newState.toJS()).toEqual(initialState);
      });

      it("Should handle NEW_PASSWORD_START", () => {
        const newState = NewPasswordReducer(undefined, {
          type: NEW_PASSWORD_START
        });

        expect(newState.toJS()).toEqual({
          loading: true,
          error: false
        });
      });

      it("Should handle NEW_PASSWORD_SUCCESS", () => {
        const newState = NewPasswordReducer(
          fromJS({
            loading: true,
            error: true
          }),
          {
            type: NEW_PASSWORD_SUCCESS
          }
        );

        expect(newState.toJS()).toEqual({
          loading: false,
          error: false
        });
      });

      it("Should handle NEW_PASSWORD_FAIL", () => {
        const err = "New Password loading error";
        const newState = NewPasswordReducer(
          fromJS({
            loading: true,
            error: true
          }),
          {
            type: NEW_PASSWORD_FAIL,
            error: err
          }
        );

        expect(newState.toJS()).toEqual({
          loading: false,
          error: err
        });
      });
    });
  });
});
