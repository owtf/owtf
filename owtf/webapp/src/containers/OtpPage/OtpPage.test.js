import React from "react";
import { shallow } from "enzyme";
import toJson from "enzyme-to-json";
import "../../setupTests";
import { findByTestAtrr, checkProps } from "../../utils/testUtils";
import { OtpPage } from "./index";
import { fromJS } from "immutable";

import { otpSuccess, otpFail } from "./actions";
import { OTP_START, OTP_SUCCESS, OTP_FAIL } from "./constants";

import { postDataToOtpAPI } from "./saga";
import { runSaga } from "redux-saga";
import * as api from "./api";

import { otpReducer } from "./reducer";

describe("OtpPage component", () => {
  describe("Testing dumb otp component", () => {
    let wrapper;
    let props;
    beforeEach(() => {
      props = {
        onSubmit: jest.fn(),
        onResend: jest.fn(),
        email: "test_user@test.com"
      };
      wrapper = shallow(<OtpPage {...props} />);
    });
    it("Should have correct prop-types", () => {
      const expectedProps = {
        onSubmit: () => {},
        onResend: () => {},
        email: "test_user@test.com"
      };
      const propsErr = checkProps(OtpPage, expectedProps);
      expect(propsErr).toBeUndefined();
    });

    it("Should render without errors", () => {
      const component = findByTestAtrr(wrapper, "otpPageComponent");
      expect(component.length).toBe(1);
      expect(toJson(component)).toMatchSnapshot();
    });

    it("Should correctly render its sub-components", () => {
      wrapper.setState({
        otp: "123456",
        otpError: ""
      });
      const div = wrapper.find("div");
      const heading = wrapper.find("h2");
      const textInputField = wrapper.find("input");
      const paragraph = wrapper.find("p");
      const button = wrapper.find("button");

      expect(div.length).toBe(5);
      expect(heading.length).toBe(1);
      expect(heading.at(0).props().children).toEqual("A code was sent");
      expect(textInputField.length).toBe(1);
      expect(paragraph.length).toBe(5);
      expect(paragraph.at(0).props().children).toEqual(
        "Enter the 6-digit verification code sent to your email."
      );

      expect(paragraph.at(2).props().children.props.children).toEqual(
        "Resend Code"
      );
      expect(paragraph.at(3).props().children.props.children).toEqual(
        "Change Username / Email"
      );
      expect(paragraph.at(4).props().children).toEqual(
        "If you don't find it in your inbox, check spam folder."
      );
      expect(button.length).toBe(1);
      expect(button.at(0).props().children).toEqual("Submit");
      expect(button.at(0).props().disabled).toEqual(false);
    });

    it("Should update state on TextInputField change event", () => {
      const otp = 123456;
      const textInputFieldUsername = wrapper.find("input").at(0);
      const eventUsername = {
        preventDefault() {},
        target: { value: otp, name: "text-input-otp" }
      };

      textInputFieldUsername.simulate("change", eventUsername);
      expect(wrapper.instance().state.otp).toEqual(otp);
    });

    it("Should call onSubmit on submit button click", () => {
      expect(props.onSubmit.mock.calls.length).toBe(0);
      const otpButton = wrapper.find("button");
      otpButton.simulate("click");
      expect(props.onSubmit.mock.calls.length).toBe(1);
    });

    it("Should call onResend on resend link click", () => {
      expect(props.onResend.mock.calls.length).toBe(0);
      const resendButton = wrapper.find("Link").at(0);
      resendButton.simulate("click");
      expect(props.onResend.mock.calls.length).toBe(1);
    });

    it("Should call handleOtpValidation to validate otp", () => {
      const textInputField = wrapper.find("input");
      textInputField.simulate("change", {
        target: { value: 12345, name: "text-input-otp" }
      });
      textInputField.simulate("blur");
      expect(wrapper.instance().state.otpError).toEqual(
        "Please enter a valid OTP"
      );
    });

    it("Should call isNumeric to check otp is valid 6-digit number", () => {
      expect(wrapper.instance().isNumeric("234sdf")).toEqual(false);
    });
  });

  describe("Testing the sagas", () => {
    describe("Testing postDataToOtpAPI saga", () => {
      let fakeAction;
      beforeEach(() => {
        fakeAction = {
          type: OTP_START,
          email: "test_user@test.com",
          otp: 123456
        };
      });

      it("Should create an otp in case of success", async () => {
        const otp = 123456;
        const successData = {
          status: "success",
          data: { status: "success", message: "Otp Send Successful" }
        };

        const dispatchedActions = [];
        api.OtpVerifyAPI = jest.fn(() =>
          jest.fn(() => Promise.resolve(successData))
        );

        const fakeStore = {
          getState: () => ({ state: "test" }),
          dispatch: action => dispatchedActions.push(action)
        };

        await runSaga(fakeStore, postDataToOtpAPI, fakeAction).done;
        expect(api.OtpVerifyAPI.mock.calls.length).toBe(1);
        expect(dispatchedActions).toContainEqual(
          otpSuccess(successData["data"]["message"], otp)
        );
      });

      it("Should handle otp error in case of failure", async () => {
        const dispatchedActions = [];
        const error = "API server is down";
        api.OtpVerifyAPI = jest.fn(() => jest.fn(() => Promise.reject(error)));

        const fakeStore = {
          getState: () => ({ state: "test" }),
          dispatch: action => dispatchedActions.push(action)
        };

        await runSaga(fakeStore, postDataToOtpAPI, fakeAction).done;
        expect(api.OtpVerifyAPI.mock.calls.length).toBe(1);
        expect(dispatchedActions).toContainEqual(otpFail(error));
      });
    });
  });

  describe("Testing reducers", () => {
    describe("Testing otpReducer", () => {
      let initialState;
      beforeEach(() => {
        initialState = {
          error: false,
          loading: false,
          otp: ""
        };
      });

      it("Should return the initial state", () => {
        const newState = otpReducer(undefined, {});
        expect(newState.toJS()).toEqual(initialState);
      });

      it("Should handle OTP_START", () => {
        const newState = otpReducer(undefined, {
          type: OTP_START
        });

        expect(newState.toJS()).toEqual({
          loading: true,
          error: false,
          otp: ""
        });
      });

      it("Should handle OTP_SUCCESS", () => {
        const otp = 123456;
        const newState = otpReducer(
          fromJS({
            loading: true,
            error: true,
            otp: ""
          }),
          {
            type: OTP_SUCCESS,
            otp: otp
          }
        );

        expect(newState.toJS()).toEqual({
          loading: false,
          error: false,
          otp: otp
        });
      });

      it("Should handle OTP_FAIL", () => {
        const err = "Test sessions loading error";
        const newState = otpReducer(
          fromJS({
            loading: true,
            error: true,
            otp: ""
          }),
          {
            type: OTP_FAIL,
            error: err
          }
        );

        expect(newState.toJS()).toEqual({
          loading: false,
          error: err,
          otp: ""
        });
      });
    });
  });
});
