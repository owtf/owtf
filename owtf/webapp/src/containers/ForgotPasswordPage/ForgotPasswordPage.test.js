import React from "react";
import { shallow } from "enzyme";
import toJson from "enzyme-to-json";
import "../../setupTests";
import { findByTestAtrr, checkProps } from "../../utils/testUtils";
import { ForgotPasswordPage } from "./index";
import { fromJS } from "immutable";
import { forgotPasswordEmailSuccess, forgotPasswordEmailFail } from "./actions";
import {
  FORGOT_PASSWORD_EMAIL_FAIL,
  FORGOT_PASSWORD_EMAIL_START,
  FORGOT_PASSWORD_EMAIL_SUCCESS
} from "./constants";
import { postDataToEmailAPI } from "./saga";
import { runSaga } from "redux-saga";
import * as api from "./api";
import { forgotPasswordEmailReducer } from "./reducer";

describe("ForgotPasswordPage component", () => {
  describe("Testing dumb forgot password component", () => {
    let wrapper;
    let props;

    beforeEach(() => {
      props = {
        onReset: jest.fn()
      };
      wrapper = shallow(<ForgotPasswordPage {...props} />);
    });

    it("Should have correct prop-types", () => {
      const expectedProps = {
        onReset: () => {}
      };
      const propsErr = checkProps(ForgotPasswordPage, expectedProps);
      expect(propsErr).toBeUndefined();
    });

    it("Should render without errors", () => {
      const component = findByTestAtrr(wrapper, "forgotPasswordPageComponent");
      expect(component.length).toBe(1);
      expect(toJson(component)).toMatchSnapshot();
    });

    it("Should correctly render its sub-components", () => {
      wrapper.setState({
        emailOrUsername: "",
        emailError: ""
      });
      const div = wrapper.find("div");
      const heading = wrapper.find("h2");
      const textInputField = wrapper.find("input");
      const paragraph = wrapper.find("p");
      const button = wrapper.find("button");

      expect(div.length).toBe(5);
      expect(heading.length).toBe(1);
      expect(heading.at(0).props().children).toEqual("Forgot Password?");
      expect(textInputField.length).toBe(1);
      expect(paragraph.length).toBe(2);
      expect(paragraph.at(0).props().children).toEqual(
        "Reset password in 2 quick steps."
      );
      expect(div.at(4).props().children.props.children).toEqual("Back");
      expect(button.length).toBe(1);
      expect(button.at(0).props().children).toEqual("Reset Password");
      expect(button.at(0).props().disabled).toEqual(false);
    });

    it("Should update state on TextInputField change event", () => {
      const emailOrUsername = "test_user@test.com";
      const textInputField = wrapper.find("input").at(0);
      const event = {
        preventDefault() {},
        target: { value: emailOrUsername, name: "text-input-email-or-username" }
      };

      textInputField.simulate("change", event);
      expect(wrapper.instance().state.emailOrUsername).toEqual(emailOrUsername);
    });

    it("Should call onReset on reset password button click", () => {
      expect(props.onReset.mock.calls.length).toBe(0);
      const resetPasswordButton = wrapper.find("button");
      resetPasswordButton.simulate("click");
      expect(props.onReset.mock.calls.length).toBe(1);
    });
  });

  describe("Testing the sagas", () => {
    describe("Testing postDataToEmailAPI saga", () => {
      let fakeAction;
      beforeEach(() => {
        fakeAction = {
          type: FORGOT_PASSWORD_EMAIL_START,
          emailOrUsername: "test_user@test.com",
          otp: 123456
        };
      });

      it("Should generate an otp in case of success", async () => {
        const emailOrUsername = "test_user@test.com";
        const successData = {
          status: "success",
          data: { status: "success", message: "Otp Send Successful" }
        };

        const dispatchedActions = [];
        api.emailAPI = jest.fn(() =>
          jest.fn(() => Promise.resolve(successData))
        );

        const fakeStore = {
          getState: () => ({ state: "test" }),
          dispatch: action => dispatchedActions.push(action)
        };

        await runSaga(fakeStore, postDataToEmailAPI, fakeAction).done;
        expect(api.emailAPI.mock.calls.length).toBe(1);
        expect(dispatchedActions).toContainEqual(
          forgotPasswordEmailSuccess(
            successData["data"]["message"],
            emailOrUsername
          )
        );
      });

      it("Should handle otp error in case of failure", async () => {
        const dispatchedActions = [];
        const error = "API server is down";
        api.emailAPI = jest.fn(() => jest.fn(() => Promise.reject(error)));

        const fakeStore = {
          getState: () => ({ state: "test" }),
          dispatch: action => dispatchedActions.push(action)
        };

        await runSaga(fakeStore, postDataToEmailAPI, fakeAction).done;
        expect(api.emailAPI.mock.calls.length).toBe(1);
        expect(dispatchedActions).toContainEqual(
          forgotPasswordEmailFail(error)
        );
      });
    });
  });

  describe("Testing reducers", () => {
    describe("forgotPasswordEmailReducer", () => {
      let initialState;
      beforeEach(() => {
        initialState = {
          error: false,
          loading: false,
          emailOrUsername: null
        };
      });

      it("Should return the initial state", () => {
        const newState = forgotPasswordEmailReducer(undefined, {});
        expect(newState.toJS()).toEqual(initialState);
      });

      it("Should handle FORGOT_PASSWORD_EMAIL_START", () => {
        const newState = forgotPasswordEmailReducer(undefined, {
          type: FORGOT_PASSWORD_EMAIL_START
        });

        expect(newState.toJS()).toEqual({
          loading: true,
          error: false,
          emailOrUsername: null
        });
      });

      it("Should handle FORGOT_PASSWORD_EMAIL_SUCCESS", () => {
        const msg = "Forgot Password Success";
        const emailOrUsername = "test_user@test.com";
        const newState = forgotPasswordEmailReducer(
          fromJS({
            loading: true,
            error: true,
            emailOrUsername: null
          }),
          {
            type: FORGOT_PASSWORD_EMAIL_SUCCESS,
            msg: msg,
            emailOrUsername: emailOrUsername
          }
        );

        expect(newState.toJS()).toEqual({
          loading: false,
          error: false,
          emailOrUsername: emailOrUsername
        });
      });

      it("Should handle FORGOT_PASSWORD_EMAIL_FAIL", () => {
        const err = "Forgot Password loading error";
        const newState = forgotPasswordEmailReducer(
          fromJS({
            loading: true,
            error: true,
            emailOrUsername: null
          }),
          {
            type: FORGOT_PASSWORD_EMAIL_FAIL,
            error: err
          }
        );

        expect(newState.toJS()).toEqual({
          loading: false,
          error: err,
          emailOrUsername: null
        });
      });
    });
  });
});
